from django.db import transaction
from django.utils import timezone

from .models import OnboardingRun, RunEvent, WorkflowStep


DEMO_ORGANIZATIONS = [
    {
        "slug": "northstar-models",
        "name": "Northstar Models",
        "entity_type": "Model",
        "description": "Onboards new talent across the agency roster, portfolio, calendar, and communications.",
        "required_fields": ["name", "email", "location", "availability"],
        "integrations": [
            {"name": "Agency database", "type": "Demo database", "status": "connected"},
            {"name": "Google Drive", "type": "Drive", "status": "connected"},
            {"name": "Booking calendar", "type": "Google Calendar", "status": "connected"},
            {"name": "Portfolio CMS", "type": "Demo CMS", "status": "simulated"},
            {"name": "Agency inbox", "type": "Gmail", "status": "connected"},
        ],
        "workflow": [
            {"key": "extract", "title": "Extract & validate information", "capability": "extract_entity_information", "tool": "Gemini extractor", "requires": ["name", "location"]},
            {"key": "record", "title": "Create agency record", "capability": "create_internal_record", "tool": "Demo database", "requires": ["name"]},
            {"key": "drive", "title": "Create Drive folder", "capability": "create_folder", "tool": "Google Drive", "requires": ["name"]},
            {"key": "calendar", "title": "Create booking calendar", "capability": "create_calendar", "tool": "Google Calendar", "requires": ["email", "availability"]},
            {"key": "profile", "title": "Publish portfolio profile", "capability": "create_public_profile", "tool": "Demo CMS", "requires": ["name", "location"]},
            {"key": "notify", "title": "Notify agency team", "capability": "send_notification", "tool": "Gmail", "requires": ["email"]},
            {"key": "verify", "title": "Verify onboarding", "capability": "verify_operation", "tool": "ADK verifier", "requires": []},
        ],
    },
    {
        "slug": "aurora-records",
        "name": "Aurora Records",
        "entity_type": "Artist",
        "description": "Coordinates newly signed artists across the roster, release workspace, calendar, and A&R team.",
        "required_fields": ["name", "email", "genre", "manager"],
        "integrations": [
            {"name": "Artist roster", "type": "Demo database", "status": "connected"},
            {"name": "Artist workspace", "type": "Google Drive", "status": "connected"},
            {"name": "Release calendar", "type": "Google Calendar", "status": "connected"},
            {"name": "Roster website", "type": "Demo CMS", "status": "simulated"},
            {"name": "A&R alerts", "type": "Gmail", "status": "connected"},
        ],
        "workflow": [
            {"key": "extract", "title": "Extract & validate information", "capability": "extract_entity_information", "tool": "Gemini extractor", "requires": ["name", "genre"]},
            {"key": "record", "title": "Create artist record", "capability": "create_internal_record", "tool": "Demo database", "requires": ["name"]},
            {"key": "drive", "title": "Create artist workspace", "capability": "create_folder", "tool": "Google Drive", "requires": ["name"]},
            {"key": "profile", "title": "Publish roster profile", "capability": "create_public_profile", "tool": "Demo CMS", "requires": ["name", "genre"]},
            {"key": "calendar", "title": "Create release calendar", "capability": "create_calendar", "tool": "Google Calendar", "requires": ["email"]},
            {"key": "notify", "title": "Notify A&R team", "capability": "send_notification", "tool": "Gmail", "requires": ["email", "manager"]},
            {"key": "verify", "title": "Verify onboarding", "capability": "verify_operation", "tool": "ADK verifier", "requires": []},
        ],
    },
]


def ensure_demo_data():
    from .models import Organization

    for config in DEMO_ORGANIZATIONS:
        Organization.objects.update_or_create(slug=config["slug"], defaults=config)


def create_run(organization, data, source_text=""):
    entity_name = data.get("name") or f"New {organization.entity_type}"
    with transaction.atomic():
        run = OnboardingRun.objects.create(
            organization=organization,
            entity_name=entity_name,
            entity_data=data,
            source_text=source_text,
            status=OnboardingRun.Status.RUNNING,
        )
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
    if run.status not in {OnboardingRun.Status.RUNNING, OnboardingRun.Status.FAILED}:
        return run

    step = run.steps.exclude(status=WorkflowStep.Status.COMPLETED).first()
    if not step:
        run.status = OnboardingRun.Status.COMPLETED
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "completed_at", "updated_at"])
        return run

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

    step.status = WorkflowStep.Status.COMPLETED
    step.attempt_count += 1
    step.started_at = step.started_at or timezone.now()
    step.completed_at = timezone.now()
    step.summary = _summary_for(step)
    step.result = {"adapter": step.tool_name, "idempotency_key": f"{run.id}:{step.key}", "verified": True}
    step.save()
    RunEvent.objects.create(run=run, kind="success", message=step.summary, metadata={"step": step.key})

    if not run.steps.exclude(status=WorkflowStep.Status.COMPLETED).exists():
        run.status = OnboardingRun.Status.COMPLETED
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "completed_at", "updated_at"])
        RunEvent.objects.create(run=run, kind="complete", message="Every operation returned a verified result. Onboarding is complete.")
    return run


def resume_run(run, supplied):
    entity_data = dict(run.entity_data)
    entity_data.update({key: value.strip() for key, value in supplied.items() if value.strip()})
    run.entity_data = entity_data
    run.missing_fields = []
    run.status = OnboardingRun.Status.RUNNING
    run.steps.filter(status=WorkflowStep.Status.BLOCKED).update(status=WorkflowStep.Status.PENDING, summary="")
    run.save(update_fields=["entity_data", "missing_fields", "status", "updated_at"])
    RunEvent.objects.create(run=run, kind="resume", message="Missing information received. Resuming from the paused step; completed work will not be repeated.")
    return run


def _summary_for(step):
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
