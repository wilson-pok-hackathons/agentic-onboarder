# from django.contrib.auth import get_user_model
# from django.test import TestCase
# from django.urls import reverse

# from .models import (
#     Field,
#     OnboardingRun,
#     Organization,
#     OrganizationField,
#     WorkflowStep,
# )
# from .services import (
#     advance_run,
#     create_run,
#     resume_run,
#     save_organization_config,
# )


# class ProductFlowTests(TestCase):
#     def setUp(self):
#         User = get_user_model()

#         self.user = User.objects.create_user(
#             username="testuser",
#             password="test-password-123",
#         )
#         self.other_user = User.objects.create_user(
#             username="otheruser",
#             password="other-password-123",
#         )

#         self.name_field = Field.objects.create(
#             key="name",
#             label="Name",
#             type="text",
#         )
#         self.email_field = Field.objects.create(
#             key="email",
#             label="Email",
#             type="email",
#         )
#         self.availability_field = Field.objects.create(
#             key="availability",
#             label="Availability",
#             type="text",
#         )

#         self.organization = Organization.objects.create(
#             owner=self.user,
#             slug="northstar-models",
#             name="Northstar Models",
#             entity_type="Model",
#             description="Test modeling agency",
#             workflow=[
#                 {
#                     "key": "extract",
#                     "title": "Extract information",
#                     "capability": "extract_entity_information",
#                     "tool": "Demo extractor",
#                     "requires": ["name"],
#                 },
#                 {
#                     "key": "calendar",
#                     "title": "Create booking calendar",
#                     "capability": "create_calendar",
#                     "tool": "Demo calendar",
#                     "requires": ["email", "availability"],
#                 },
#                 {
#                     "key": "verify",
#                     "title": "Verify onboarding",
#                     "capability": "verify_operation",
#                     "tool": "Demo verifier",
#                     "requires": [],
#                 },
#             ],
#         )

#         OrganizationField.objects.create(
#             organization=self.organization,
#             field=self.name_field,
#             required=True,
#         )
#         OrganizationField.objects.create(
#             organization=self.organization,
#             field=self.email_field,
#             required=True,
#         )
#         OrganizationField.objects.create(
#             organization=self.organization,
#             field=self.availability_field,
#             required=True,
#         )

#         self.organization.fields.set(
#             [
#                 self.name_field,
#                 self.email_field,
#                 self.availability_field,
#             ]
#         )

#         self.other_organization = Organization.objects.create(
#             owner=self.other_user,
#             slug="other-organization",
#             name="Other Organization",
#             entity_type="Employee",
#             workflow=[],
#         )

#         self.client.force_login(self.user)

#     def test_anonymous_user_is_redirected_to_login(self):
#         self.client.logout()

#         response = self.client.get(reverse("dashboard"))

#         self.assertRedirects(
#             response,
#             f"{reverse('login')}?next={reverse('dashboard')}",
#         )

#     def test_dashboard_only_lists_current_users_organizations(self):
#         response = self.client.get(reverse("dashboard"))

#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, "core/dashboard.html")
#         self.assertContains(response, "Northstar Models")
#         self.assertNotContains(response, "Other Organization")

#     def test_organization_setup_renders(self):
#         response = self.client.get(
#             reverse(
#                 "organization_setup",
#                 args=[self.organization.slug],
#             )
#         )

#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, "core/setup.html")
#         self.assertEqual(
#             response.context["organization"],
#             self.organization,
#         )

#     def test_add_organization_assigns_current_user(self):
#         response = self.client.post(
#             reverse("add_organization"),
#             {
#                 "name": "Phoenix Talent",
#                 "entity_type": "Model",
#                 "description": "A new organization",
#             },
#         )

#         organization = Organization.objects.get(
#             slug="phoenix-talent"
#         )

#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(organization.owner, self.user)
#         self.assertEqual(organization.entity_type, "Model")
#         self.assertRedirects(
#             response,
#             reverse(
#                 "organization_setup",
#                 args=[organization.slug],
#             ),
#         )

#     def test_required_fields_come_from_bridge_table(self):
#         self.assertCountEqual(
#             self.organization.required_fields,
#             ["name", "email", "availability"],
#         )

#     def test_save_organization_config_updates_fields(self):
#         save_organization_config(
#             self.organization,
#             selected_field_keys=["name", "email"],
#             required_field_keys=["email"],
#         )

#         self.organization.refresh_from_db()

#         self.assertCountEqual(
#             self.organization.fields.values_list(
#                 "key",
#                 flat=True,
#             ),
#             ["name", "email"],
#         )
#         self.assertEqual(
#             self.organization.required_fields,
#             ["email"],
#         )

#     def test_create_run_snapshots_configured_workflow(self):
#         run = create_run(
#             self.organization,
#             {
#                 "name": "Ari Stone",
#                 "email": "ari@example.com",
#                 "availability": "Flexible",
#             },
#         )

#         self.assertEqual(
#             run.status,
#             OnboardingRun.Status.RUNNING,
#         )
#         self.assertEqual(
#             run.steps.count(),
#             len(self.organization.workflow),
#         )
#         self.assertEqual(
#             list(run.steps.values_list("key", flat=True)),
#             ["extract", "calendar", "verify"],
#         )
#         self.assertTrue(run.events.filter(kind="start").exists())

#     def test_run_pauses_and_resumes_without_repeating_work(self):
#         run = create_run(
#             self.organization,
#             {
#                 "name": "Jordan Lee",
#                 "email": "",
#                 "availability": "Weekdays",
#             },
#         )

#         # Complete the first step.
#         advance_run(run)

#         first_step = run.steps.get(key="extract")
#         first_step.refresh_from_db()

#         self.assertEqual(
#             first_step.status,
#             WorkflowStep.Status.COMPLETED,
#         )
#         self.assertEqual(first_step.attempt_count, 1)

#         # The calendar step should pause because email is missing.
#         advance_run(run)
#         run.refresh_from_db()

#         self.assertEqual(
#             run.status,
#             OnboardingRun.Status.WAITING,
#         )
#         self.assertEqual(run.missing_fields, ["email"])

#         resume_run(
#             run,
#             {"email": "jordan@example.com"},
#         )

#         run.refresh_from_db()

#         self.assertEqual(
#             run.status,
#             OnboardingRun.Status.RUNNING,
#         )
#         self.assertEqual(
#             run.entity_data["email"],
#             "jordan@example.com",
#         )

#         # Complete the calendar and verification steps.
#         advance_run(run)
#         advance_run(run)
#         run.refresh_from_db()
#         first_step.refresh_from_db()

#         self.assertEqual(
#             run.status,
#             OnboardingRun.Status.COMPLETED,
#         )

#         # Previously completed work must not run again.
#         self.assertEqual(first_step.attempt_count, 1)
#         self.assertEqual(run.progress, 100)

#     def test_new_onboarding_endpoint_creates_run(self):
#         response = self.client.post(
#             reverse("new_onboarding"),
#             {
#                 "organization": self.organization.slug,
#                 "name": "Ari Stone",
#                 "email": "ari@example.com",
#                 "availability": "Flexible",
#                 "source_text": "Submitted through a test.",
#             },
#         )

#         run = OnboardingRun.objects.get(
#             entity_name="Ari Stone"
#         )

#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(
#             run.organization,
#             self.organization,
#         )
#         self.assertEqual(
#             run.entity_data["email"],
#             "ari@example.com",
#         )
#         self.assertEqual(
#             run.steps.count(),
#             len(self.organization.workflow),
#         )
#         self.assertRedirects(
#             response,
#             reverse("run_detail", args=[run.id]),
#         )