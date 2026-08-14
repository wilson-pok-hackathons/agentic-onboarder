from django.contrib import admin

from .models import OnboardingRun, Organization, RunEvent, WorkflowStep


admin.site.register(Organization)
admin.site.register(OnboardingRun)
admin.site.register(WorkflowStep)
admin.site.register(RunEvent)
