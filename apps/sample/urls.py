from django.urls import path
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path("dashboard/", views.DashboardOverviewPage.as_view(), name="index"),
    # path("dashboard-guest/", views.GuestDashboardOverviewPage.as_view(), name="index_guest"),
    path("pulse/", views.DashboardPulseAPI.as_view(), name="dashboard_pulse"),
]
