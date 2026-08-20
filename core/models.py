import uuid

from django.db import models


class Organization(models.Model):
    """A tenant/customer and the reusable configuration for its agent.

    The workflow is stored as JSON because different organizations can have
    different fields and actions without requiring a new Django model for each
    industry (for example, models versus recording artists).
    """

    # `slug` is the URL-safe identifier used in routes such as
    # /setup/northstar-models/. The human-readable name can change safely.
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=160)
    entity_type = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    required_fields = models.JSONField(default=list)
    workflow = models.JSONField(default=list)
    integrations = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class OnboardingRun(models.Model):
    """One concrete attempt to onboard one person/entity.

    Organization holds the reusable recipe; OnboardingRun holds the live data
    and overall state for one execution of that recipe.
    """

    class Status(models.TextChoices):
        # TextChoices keeps database values stable while providing friendly
        # labels through `run.get_status_display()` in templates.
        DRAFT = "draft", "Draft"
        RUNNING = "running", "Running"
        WAITING = "waiting_for_input", "Needs input"
        FAILED = "failed", "Failed"
        COMPLETED = "completed", "Completed"

    # UUIDs are safer to expose in URLs than predictable integer IDs.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Deleting an organization also deletes its runs (`CASCADE`). The
    # `related_name` enables reverse queries such as organization.runs.all().
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="runs")
    entity_name = models.CharField(max_length=160)
    # Flexible extracted/form data: {"name": ..., "email": ..., ...}.
    entity_data = models.JSONField(default=dict)
    source_text = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    missing_fields = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def progress(self):
        """Return a display-ready completion percentage from 0 through 100."""
        # `self.steps` exists because WorkflowStep.run uses related_name="steps".
        total = self.steps.count()
        complete = self.steps.filter(status=WorkflowStep.Status.COMPLETED).count()
        return round((complete / total) * 100) if total else 0

    def __str__(self):
        return f"{self.entity_name} · {self.organization.entity_type}"


class WorkflowStep(models.Model):
    """A single tool action belonging to an OnboardingRun.

    Steps are copied from the organization configuration when a run starts.
    That snapshot prevents later configuration edits from changing a run that
    is already in progress.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        BLOCKED = "blocked", "Blocked"
        FAILED = "failed", "Failed"
        COMPLETED = "completed", "Complete"

    run = models.ForeignKey(OnboardingRun, on_delete=models.CASCADE, related_name="steps")
    # `key` is the stable machine identifier; `title` is presentation text.
    key = models.SlugField()
    title = models.CharField(max_length=160)
    # Capability describes WHAT to do; tool_name describes WHICH adapter does
    # it. This separation lets create_calendar map to Google Calendar today and
    # another calendar provider later.
    capability = models.CharField(max_length=100)
    tool_name = models.CharField(max_length=120, default="Demo adapter")
    position = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Entity-data keys that must be present before this step can execute.
    requires = models.JSONField(default=list)
    summary = models.TextField(blank=True)
    result = models.JSONField(default=dict)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Calling run.steps.all() automatically returns execution-plan order.
        ordering = ["position"]
        # A run cannot accidentally contain two steps with the same key.
        constraints = [models.UniqueConstraint(fields=["run", "key"], name="unique_run_step")]

    def __str__(self):
        return self.title


class RunEvent(models.Model):
    """Append-only activity/history entry for explaining what the agent did."""

    run = models.ForeignKey(OnboardingRun, on_delete=models.CASCADE, related_name="events")
    kind = models.CharField(max_length=40, default="info")
    message = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Activity feeds show the newest event first by default.
        ordering = ["-created_at"]
