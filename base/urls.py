from django.urls import path
from . import views


urlpatterns = [
    path("", views.package, name="front_package")
]
