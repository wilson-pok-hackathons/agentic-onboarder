from django.urls import path

from . import views

urlpatterns = [
    # Full-page routes shown directly in the browser.
    path("", views.dashboard, name="dashboard"),
    path("setup/", views.organization_setup, name="setup"),
    path("setup/<slug:slug>/", views.organization_setup, name="organization_setup"),
    path("onboard/", views.new_onboarding, name="new_onboarding"),
    path("runs/<uuid:run_id>/", views.run_detail, name="run_detail"),

    # Supporting routes used by the live run page. `state` returns an HTML
    # fragment; `advance` and `resume` mutate workflow state via POST requests.
    path("runs/<uuid:run_id>/state/", views.run_state, name="run_state"),
    path("runs/<uuid:run_id>/advance/", views.run_advance, name="run_advance"),
    path("runs/<uuid:run_id>/resume/", views.run_resume, name="run_resume"),
]
