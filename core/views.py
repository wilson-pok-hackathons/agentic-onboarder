from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import OnboardingRun, Organization
from .services import advance_run, create_run, ensure_demo_data, resume_run


def dashboard(request):
    ensure_demo_data()
    organizations = Organization.objects.filter(is_active=True)
    runs = OnboardingRun.objects.select_related("organization").all().order_by("-created_at")[:8]
    counts = {key: OnboardingRun.objects.filter(status=value).count() for key, value in {
        "active": OnboardingRun.Status.RUNNING,
        "attention": OnboardingRun.Status.WAITING,
        "completed": OnboardingRun.Status.COMPLETED,
        "failed": OnboardingRun.Status.FAILED,
    }.items()}
    return render(request, "core/dashboard.html", {"organizations": organizations, "runs": runs, "counts": counts, "page": "dashboard"})


def organization_setup(request, slug=None):
    ensure_demo_data()
    organization = get_object_or_404(Organization, slug=slug) if slug else Organization.objects.first()
    return render(request, "core/setup.html", {"organization": organization, "organizations": Organization.objects.all(), "page": "setup"})


def new_onboarding(request):
    ensure_demo_data()
    organizations = Organization.objects.filter(is_active=True)
    selected = request.GET.get("organization") or request.POST.get("organization")
    organization = organizations.filter(slug=selected).first() or organizations.first()
    if request.method == "POST":
        organization = get_object_or_404(Organization, slug=request.POST.get("organization"))
        data = {field: request.POST.get(field, "").strip() for field in organization.required_fields}
        data["name"] = request.POST.get("name", "").strip()
        if not data["name"]:
            messages.error(request, "A name is required to create the onboarding run.")
        else:
            run = create_run(organization, data, request.POST.get("source_text", ""))
            return redirect("run_detail", run_id=run.id)
    return render(request, "core/new_onboarding.html", {"organizations": organizations, "organization": organization, "page": "new"})


def run_detail(request, run_id):
    run = get_object_or_404(OnboardingRun.objects.select_related("organization"), id=run_id)
    return render(request, "core/run_detail.html", {"run": run, "page": "runs"})


def run_state(request, run_id):
    run = get_object_or_404(OnboardingRun, id=run_id)
    return render(request, "core/partials/run_state.html", {"run": run})


@require_POST
def run_advance(request, run_id):
    run = get_object_or_404(OnboardingRun, id=run_id)
    advance_run(run)
    run.refresh_from_db()
    return JsonResponse({"status": run.status, "progress": run.progress})


@require_POST
def run_resume(request, run_id):
    run = get_object_or_404(OnboardingRun, id=run_id)
    if run.status != OnboardingRun.Status.WAITING:
        return HttpResponseBadRequest("Run is not waiting for input.")
    supplied = {field: request.POST.get(field, "") for field in run.missing_fields}
    if any(not value.strip() for value in supplied.values()):
        messages.error(request, "Please provide every requested field.")
        return redirect("run_detail", run_id=run.id)
    resume_run(run, supplied)
    return redirect("run_detail", run_id=run.id)
