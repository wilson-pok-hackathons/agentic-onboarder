import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0002_person_age")]
    operations = [
        migrations.CreateModel(name="Organization", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("slug", models.SlugField(unique=True)), ("name", models.CharField(max_length=160)),
            ("entity_type", models.CharField(max_length=80)), ("description", models.TextField(blank=True)),
            ("required_fields", models.JSONField(default=list)), ("workflow", models.JSONField(default=list)),
            ("integrations", models.JSONField(default=list)), ("is_active", models.BooleanField(default=True)),
        ]),
        migrations.CreateModel(name="OnboardingRun", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("entity_name", models.CharField(max_length=160)), ("entity_data", models.JSONField(default=dict)),
            ("source_text", models.TextField(blank=True)),
            ("status", models.CharField(choices=[("draft", "Draft"), ("running", "Running"), ("waiting_for_input", "Needs input"), ("failed", "Failed"), ("completed", "Completed")], default="draft", max_length=32)),
            ("missing_fields", models.JSONField(default=list)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)), ("completed_at", models.DateTimeField(blank=True, null=True)),
            ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="runs", to="core.organization")),
        ]),
        migrations.CreateModel(name="RunEvent", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("kind", models.CharField(default="info", max_length=40)), ("message", models.TextField()),
            ("metadata", models.JSONField(default=dict)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="core.onboardingrun")),
        ], options={"ordering": ["-created_at"]}),
        migrations.CreateModel(name="WorkflowStep", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("key", models.SlugField()), ("title", models.CharField(max_length=160)), ("capability", models.CharField(max_length=100)),
            ("tool_name", models.CharField(default="Demo adapter", max_length=120)), ("position", models.PositiveSmallIntegerField()),
            ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("blocked", "Blocked"), ("failed", "Failed"), ("completed", "Complete")], default="pending", max_length=20)),
            ("requires", models.JSONField(default=list)), ("summary", models.TextField(blank=True)),
            ("result", models.JSONField(default=dict)), ("attempt_count", models.PositiveSmallIntegerField(default=0)),
            ("started_at", models.DateTimeField(blank=True, null=True)), ("completed_at", models.DateTimeField(blank=True, null=True)),
            ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="steps", to="core.onboardingrun")),
        ], options={"ordering": ["position"]}),
        migrations.AddConstraint(model_name="workflowstep", constraint=models.UniqueConstraint(fields=("run", "key"), name="unique_run_step")),
        migrations.DeleteModel(name="Person"),
    ]
