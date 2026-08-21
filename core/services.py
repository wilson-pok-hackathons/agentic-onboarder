'''
Business logic layer

Contains python functions that execute the actual logic of of the application. Complex workflows,
external API calls, and heavy calc

views.py -> calls services.py -> manipulates models.py -> returns raw data to view
'''



from django.db import transaction
from django.utils import timezone

from .models import Field, Organization, OrganizationField, OnboardingRun, RunEvent, WorkflowStep



################################################
### Probably aactual useful stuff down here ###

def save_organization_config(organization, selected_field_keys, required_field_keys):
    """Synchronizes an organiations selected and required fields by setting up new rows in
    the OrganizationField table
    """
    with transaction.atomic():
        # clear out any existing required fields for this org
        OrganizationField.objects.filter(organization=organization).delete()

        # get the actual Field objects from the Field table based on user choices
        active_fields = Field.objects.filter(key__in=selected_field_keys)

        # create new OrganizationField rows
        new_brdige_rows = []
        for field in active_fields:
        # check for required flag
            is_required = field.key in required_field_keys

            new_brdige_rows.append(
                OrganizationField(
                    organization = organization,
                    field = field,
                    required = is_required
                )
            )

        # insert new rows into table
        OrganizationField.objects.bulk_create(new_brdige_rows)

        # sync Django's ManyToMany fields
        organization.fields.set(active_fields)


def create_run(organization, data, source_text=""):
    """Create a run and snapshot its organization's workflow into step rows."""
    entity_name = data.get("name") or f"New {organization.entity_type}"
    # Every enclosed database write succeeds or rolls back as one unit. We never
    # want a run saved with only half of its configured steps.
    with transaction.atomic():
        run = OnboardingRun.objects.create(
            organization=organization,
            entity_name=entity_name,
            entity_data=data,
            source_text=source_text,
            status=OnboardingRun.Status.RUNNING,
        )
        # Convert the reusable JSON recipe into independently updateable rows
        # for this particular execution.
        for index, item in enumerate(organization.workflow):
            WorkflowStep.objects.create(
                run=run,
                key=item["key"],
                title=item["title"],
                capability=item["capability"],
                tool_name=item.get("tool", "Demo adapter"),
                requires=item.get("requires", []),
                position=index,
            )
        RunEvent.objects.create(run=run, kind="start", message="Onboarding package accepted. The agent created an execution plan.")
    return run


def advance_run(run):
    """Move a run forward by no more than one workflow step."""
    # Paused/completed runs must not execute. Failed is allowed so a future
    # retry button can reuse this function.
    if run.status not in {OnboardingRun.Status.RUNNING, OnboardingRun.Status.FAILED}:
        return run

    # WorkflowStep.Meta ordering makes this the earliest unfinished action.
    step = run.steps.exclude(status=WorkflowStep.Status.COMPLETED).first()
    if not step:
        # Defensive repair for a running run that has no remaining work.
        run.status = OnboardingRun.Status.COMPLETED
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "completed_at", "updated_at"])
        return run

    # A step is eligible only when all configured required fields have values.
    missing = [field for field in step.requires if not run.entity_data.get(field)]
    if missing:
        step.status = WorkflowStep.Status.BLOCKED
        step.summary = f"Waiting for: {', '.join(missing)}"
        step.save(update_fields=["status", "summary"])
        run.status = OnboardingRun.Status.WAITING
        run.missing_fields = missing
        run.save(update_fields=["status", "missing_fields", "updated_at"])
        RunEvent.objects.create(run=run, kind="attention", message=f"Paused safely. {', '.join(missing).title()} is required before {step.title.lower()}.")
        return run

    # MVP simulation: this block stands in for a real external adapter call.
    step.status = WorkflowStep.Status.COMPLETED
    step.attempt_count += 1
    step.started_at = step.started_at or timezone.now()
    step.completed_at = timezone.now()
    step.summary = _summary_for(step)
    # A stable run+step key lets real APIs recognize retries and avoid creating
    # duplicate folders, calendars, profiles, or notifications.
    step.result = {"adapter": step.tool_name, "idempotency_key": f"{run.id}:{step.key}", "verified": True}
    step.save()
    RunEvent.objects.create(run=run, kind="success", message=step.summary, metadata={"step": step.key})

    # `exists()` asks a cheap yes/no database question without loading all rows.
    if not run.steps.exclude(status=WorkflowStep.Status.COMPLETED).exists():
        run.status = OnboardingRun.Status.COMPLETED
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "completed_at", "updated_at"])
        RunEvent.objects.create(run=run, kind="complete", message="Every operation returned a verified result. Onboarding is complete.")
    return run


def resume_run(run, supplied):
    """Merge human input into a paused run and make blocked work runnable."""
    # Copy before updating so the JSON mutation is explicit.
    entity_data = dict(run.entity_data)
    entity_data.update({key: value.strip() for key, value in supplied.items() if value.strip()})
    run.entity_data = entity_data
    run.missing_fields = []
    run.status = OnboardingRun.Status.RUNNING
    # Only blocked work is reset. Completed steps stay completed, so resume does
    # not repeat already-successful external actions.
    run.steps.filter(status=WorkflowStep.Status.BLOCKED).update(status=WorkflowStep.Status.PENDING, summary="")
    run.save(update_fields=["entity_data", "missing_fields", "status", "updated_at"])
    RunEvent.objects.create(run=run, kind="resume", message="Missing information received. Resuming from the paused step; completed work will not be repeated.")
    return run


def _summary_for(step):
    """Return safe activity text instead of exposing raw agent reasoning."""
    summaries = {
        "extract_entity_information": "Package fields extracted and validated against the organization configuration.",
        "create_internal_record": "Internal record created and its identifier stored.",
        "create_folder": "Workspace folder created with the standard organization structure.",
        "create_calendar": "Calendar created and availability rules applied.",
        "create_public_profile": "Profile draft created and published through the configured CMS adapter.",
        "send_notification": "Notification delivered to the configured team channel.",
        "verify_operation": "All tool results checked; required resources are present and addressable.",
    }
    return summaries.get(step.capability, f"{step.title} completed successfully.")
