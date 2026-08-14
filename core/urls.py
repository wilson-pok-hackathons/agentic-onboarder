from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("setup/", views.organization_setup, name="setup"),
    path("setup/<slug:slug>/", views.organization_setup, name="organization_setup"),
    path("onboard/", views.new_onboarding, name="new_onboarding"),
    path("runs/<uuid:run_id>/", views.run_detail, name="run_detail"),
    path("runs/<uuid:run_id>/state/", views.run_state, name="run_state"),
    path("runs/<uuid:run_id>/advance/", views.run_advance, name="run_advance"),
    path("runs/<uuid:run_id>/resume/", views.run_resume, name="run_resume"),
]
