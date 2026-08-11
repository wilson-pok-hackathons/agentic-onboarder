from django.shortcuts import render

# Create your views here.

from .models import Person

def home(request):
    posts = Person.objects.all().order_by("-id")

    return render(
        request,
        "core/home.html",
        {"posts": posts}
    )

