from django.urls import path
from . import views


urlpatterns = [
    # path("create/", guest_create_view, name="create"),
    path("create/", views.GuestCreatePage.as_view(), name="create"),
    path("list/", views.GuestListPage.as_view(), name="list"),
    path("<int:pk>/", views.GuestDetailPage.as_view(), name="detail"),
    path("<int:pk>/edit/", views.GuestEditPage.as_view(), name="edit"),
    path("<int:pk>/delete/", views.GuestDeleteView.as_view(), name="delete"),
]
