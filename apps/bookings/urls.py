from django.urls import path
from .views import BookingCreatePage, BookingListPage, BookingDeleteView, BookingEditPage, BookingDetailPage, BookingExportCSVView, checkout_booking
from .views_ajax import GuestSearchAPI, RoomInfoAPI, RoomAvailabilityAPI, AvailableRoomsAPI, add_payment
from . import views_payments
from . import views_invoices
from . import views_reports
from . import views_guest
from . import views

urlpatterns = [
    # Guest mode
    path(
        "guest/book/",
        views_guest.GuestBookingCreateView.as_view(),
        name="guest_booking_create",
    ),


    # path("guest/booking/success/", TemplateView.as_view(
    #     template_name="bookings/guest_booking_success.html"
    # ), name="guest_booking_success"),



    # Create page
    path("bookings/new/", BookingCreatePage.as_view(), name="booking_create"),
    path("bookings/", BookingListPage.as_view(), name="booking_list"),
    path("bookings/<int:pk>/delete/", BookingDeleteView.as_view(), name="booking_delete"),
    path("bookings/<int:pk>/edit/", BookingEditPage.as_view(), name="booking_edit"),

    path("bookings/<int:pk>/checkout/", checkout_booking, name="booking_checkout"),

    path("bookings/export/csv/", BookingExportCSVView.as_view(), name="booking_export_csv"),

    path("bookings/<int:pk>/", BookingDetailPage.as_view(), name="booking_detail"),

    # payments
    path("payments/", views_payments.PaymentListPage.as_view(), name="payment_list"),
    path("payments/<int:pk>/edit/", views_payments.PaymentEditPage.as_view(), name="payment_edit"),
    path("payments/<int:pk>/delete/", views_payments.payment_delete, name="payment_delete"),
    path("payments/<int:pk>/invoice/", views_payments.payment_invoice, name="payment_invoice"),


    # path("bookings/<int:pk>/invoice/initial/", views_invoices.booking_initial_invoice, name="booking_initial_invoice"),
    # path("bookings/<int:pk>/invoice/summary/", views_invoices.booking_invoice_summary, name="booking_invoice_summary"),
    path("bookings/<int:pk>/invoice/summary/", views_invoices.booking_invoice_summary, name="booking_invoice_summary"),


    # report
    path("reports/summary/", views_reports.ReportSummaryPage.as_view(), name="report_summary"),



    # path("dashboard/payments/<int:pk>/invoice/", views_payments.payment_invoice, name="payment_invoice"),
    # path("dashboard/payments/<int:pk>/invoice/partial/", views_payments.payment_invoice_partial, name="payment_invoice_partial"),

    # Frontend search

    path("search-rooms/", views.RoomSearchView.as_view(), name="room_search"),



    # AJAX APIs
    path("bookings/api/guests/search/", GuestSearchAPI.as_view(), name="api_guest_search"),
    path("bookings/api/rooms/info/", RoomInfoAPI.as_view(), name="api_room_info"),
    path("bookings/api/rooms/availability/", RoomAvailabilityAPI.as_view(), name="api_room_availability"),
    path("bookings/api/rooms/available/", AvailableRoomsAPI.as_view(), name="api_rooms_available"),

    path("api/bookings/<int:booking_id>/payments/add/", add_payment, name="booking_add_payment"),
]
