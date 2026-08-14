from enum import unique
import uuid

from django.db import models


class Field(models.Model):
    '''The table which describes the fields an organization can choose to collect for 
    its new onboardings 

    key: unique identifier
    label: text shown in UI
    type: description of field
    '''
    key = models.SlugField(unique=True)
    label = models.CharField(max_length=120)
    type = models.CharField(max_length=40)

    def __str__(self):
        return self.label


class Organization(models.Model):
    '''The table which describes information collected about an organization

    slug: url safe indentifier
    name: syntactically correct name of org
    entity_type: 
    description: description of organization
    fields: 
    required_fields:
    integrations:
    workflow:
    is_active:
    '''
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=160)
    entity_type = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    fields = models.ManyToManyField(Field, )
    integrations = models.JSONField(default=list)
    workflow = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class OrganizationField(models,Model):
    '''The table that acts as a join between the Field and Organization tables. Keeps
    the Field entries global and allows us to see what eeach organization requires

    organization: the org unique identifier in Organization table
    field: the field unique indentofier in Field table
    required: true if org requires field, false otherwise
    '''
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="organization_fields")
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    required = models.BooleanField(default=False)

    class Meta:
        # keeps the database from storing duplicate rows for an org<->field combo
        constraints = [models.UniqueConstraint(fields=["organization", "field"], name="unique_org_field")]


#
# mostly undderstood above here
#


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
