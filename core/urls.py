'''
Routing layer

Maps web URLs to specific views. Entry way for request to the application

User browser -> urls.py -> matches path -> dispatches to views.py
'''



from django.urls import path
from django.contrib.auth import views as auth_views

from . import views



urlpatterns = [
    # Auth
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.user_signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # Application
    path("", views.dashboard, name="dashboard"),
    # path("setup/", views.organization_setup, name="setup"),
    # path("onboard/", views.new_onboarding, name="new_onboarding"),
    # path("runs/<uuid:run_id>/", views.run_detail, name="run_detail"),

    # # Supporting routes used by the live run page. `state` returns an HTML
    # # fragment; `advance` and `resume` mutate workflow state via POST requests.
    # path("runs/<uuid:run_id>/state/", views.run_state, name="run_state"),
    # path("runs/<uuid:run_id>/advance/", views.run_advance, name="run_advance"),
    # path("runs/<uuid:run_id>/resume/", views.run_resume, name="run_resume"),
]

