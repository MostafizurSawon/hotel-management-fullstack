from django.urls import path
from . import views
from .views import (
    RoomCategoryListPage,
    CategoryCreatePage, CategoryUpdatePage, CategoryDeleteView,
    RoomCreatePage, RoomUpdatePage, RoomDeleteView,RoomOverviewPage,
)

urlpatterns = [
    # list
    path("rooms/", RoomCategoryListPage.as_view(), name="room_list"),

    # room avalablity and overview
    path("dashboard/rooms/availability/", views.RoomsAvailabilityAPI.as_view(), name="api_rooms_overview"),
    path("dashboard/rooms/overview/", views.RoomOverviewPage.as_view(), name="room_overview"),

    # path("dashboard/rooms/calendar/", views.RoomCalendarPage.as_view(), name="room_calendar"),
    path("dashboard/rooms/calendar/data/", views.RoomCalendarAPI.as_view(), name="api_room_calendar"),

    # path("dashboard/rooms/overview/", RoomOverviewPage.as_view(), name="room_overview"),
    # path("dashboard/rooms/api/availability/", RoomsAvailabilityAPI.as_view(), name="api_rooms_overview"),
    # path("dashboard/rooms/api/calendar/", RoomCalendarAPI.as_view(), name="api_room_calendar"),

    # path("rooms/overview/", RoomOverviewPage.as_view(), name="room_overview"),

    # category CRUD
    path("categories/new/", CategoryCreatePage.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", CategoryUpdatePage.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", CategoryDeleteView.as_view(), name="category_delete"),

    # room CRUD
    path("rooms/new/", RoomCreatePage.as_view(), name="room_create"),
    path("rooms/<int:pk>/edit/", RoomUpdatePage.as_view(), name="room_update"),
    path("rooms/<int:pk>/delete/", RoomDeleteView.as_view(), name="room_delete"),
]
