from django.urls import path

from .views import HealthView, MeView, PermissionProbeView

urlpatterns = [
    path("healthz", HealthView.as_view(), name="healthz"),
    path("me", MeView.as_view(), name="me"),
    path("probe/encounter-create", PermissionProbeView.as_view(), name="probe-encounter-create"),
]
