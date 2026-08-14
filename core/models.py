import uuid

from django.db import models


class Organization(models.Model):
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
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        RUNNING = "running", "Running"
        WAITING = "waiting_for_input", "Needs input"
        FAILED = "failed", "Failed"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="runs")
    entity_name = models.CharField(max_length=160)
    entity_data = models.JSONField(default=dict)
    source_text = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    missing_fields = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def progress(self):
        total = self.steps.count()
        complete = self.steps.filter(status=WorkflowStep.Status.COMPLETED).count()
        return round((complete / total) * 100) if total else 0

    def __str__(self):
        return f"{self.entity_name} · {self.organization.entity_type}"


class WorkflowStep(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        BLOCKED = "blocked", "Blocked"
        FAILED = "failed", "Failed"
        COMPLETED = "completed", "Complete"

    run = models.ForeignKey(OnboardingRun, on_delete=models.CASCADE, related_name="steps")
    key = models.SlugField()
    title = models.CharField(max_length=160)
    capability = models.CharField(max_length=100)
    tool_name = models.CharField(max_length=120, default="Demo adapter")
    position = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requires = models.JSONField(default=list)
    summary = models.TextField(blank=True)
    result = models.JSONField(default=dict)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["run", "key"], name="unique_run_step")]

    def __str__(self):
        return self.title


class RunEvent(models.Model):
    run = models.ForeignKey(OnboardingRun, on_delete=models.CASCADE, related_name="events")
    kind = models.CharField(max_length=40, default="info")
    message = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
