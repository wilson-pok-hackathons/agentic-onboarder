# from django.test import TestCase
# from django.urls import reverse
#
# from .models import OnboardingRun, Organization, WorkflowStep
# from .services import advance_run, create_run, resume_run
#
#
# class ProductFlowTests(TestCase):
#     def setUp(self):
#         self.organization = Organization.objects.get(slug="northstar-models")
#
#     def test_dashboard_and_setup_render(self):
#         self.assertContains(self.client.get(reverse("dashboard")), "Good afternoon")
#         self.assertContains(self.client.get(reverse("organization_setup", args=[self.organization.slug])), "GENERATED WORKFLOW", html=False)
#
#     def test_run_pauses_and_resumes_without_repeating_work(self):
#         run = create_run(self.organization, {"name": "Jordan Lee", "location": "Phoenix", "availability": "Weekdays", "email": ""})
#         for _ in range(5):
#             advance_run(run)
#             run.refresh_from_db()
#             if run.status == OnboardingRun.Status.WAITING:
#                 break
#
#         self.assertEqual(run.status, OnboardingRun.Status.WAITING)
#         completed_ids = list(run.steps.filter(status=WorkflowStep.Status.COMPLETED).values_list("id", flat=True))
#         attempts = dict(run.steps.filter(id__in=completed_ids).values_list("id", "attempt_count"))
#
#         resume_run(run, {"email": "jordan@example.com"})
#         for _ in range(10):
#             advance_run(run)
#             run.refresh_from_db()
#             if run.status == OnboardingRun.Status.COMPLETED:
#                 break
#
#         self.assertEqual(run.status, OnboardingRun.Status.COMPLETED)
#         self.assertTrue(all(run.steps.get(id=pk).attempt_count == count for pk, count in attempts.items()))
#
#     def test_create_endpoint_builds_configured_steps(self):
#         response = self.client.post(reverse("new_onboarding"), {
#             "organization": self.organization.slug,
#             "name": "Ari Stone",
#             "location": "Tempe",
#             "availability": "Flexible",
#             "email": "ari@example.com",
#         })
#         self.assertEqual(response.status_code, 302)
#         run = OnboardingRun.objects.get(entity_name="Ari Stone")
#         self.assertEqual(run.steps.count(), len(self.organization.workflow))
