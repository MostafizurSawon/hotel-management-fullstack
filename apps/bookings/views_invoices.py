from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, render
from django.http import HttpRequest
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from web_project import TemplateLayout, TemplateHelper

from .models import Booking
from apps.core.site_meta import get_hotel_meta

# def _ctx_base(request: HttpRequest, booking: Booking):
#     hotel_name, hotel_phone = get_hotel_meta()
#     ctx = {
#         "layout_path": TemplateHelper.set_layout("layout_blank.html", {}),  # print-friendly
#         "hotel_name": hotel_name,
#         "hotel_phone": hotel_phone,
#         "booking": booking,
#         "guest": getattr(booking, "guest", None),
#         "room": getattr(booking, "room", None),
#     }
#     # Money snapshot
#     ctx.update({
#         "rate": int(getattr(booking, "nightly_rate", 0) or 0),
#         "gross": int(getattr(booking, "gross_amount", 0) or 0),
#         "discount": int(getattr(booking, "discount_amount", 0) or 0),
#         "net": int(getattr(booking, "net_amount", 0) or 0),
#         "paid": int(getattr(booking, "payment_amount", 0) or 0),
#         "due": int(getattr(booking, "due_amount", 0) or 0),
#     })
#     return TemplateLayout.init(request, ctx)




from web_project import TemplateHelper
from apps.core.site_meta import get_hotel_meta
from .models import Booking

def _ctx_base(request, booking: Booking):
    hotel_name, hotel_phone = get_hotel_meta()
    ctx = {
        "layout_path": TemplateHelper.set_layout("layout_blank.html", {}),  # print-friendly
        "hotel_name": hotel_name,
        "hotel_phone": hotel_phone,
        "booking": booking,
        "guest": getattr(booking, "guest", None),
        "room": getattr(booking, "room", None),

        "rate": int(getattr(booking, "nightly_rate", 0) or 0),
        "gross": int(getattr(booking, "gross_amount", 0) or 0),
        "discount": int(getattr(booking, "discount_amount", 0) or 0),
        "net": int(getattr(booking, "net_amount", 0) or 0),
        "paid": int(getattr(booking, "payment_amount", 0) or 0),
        "due": int(getattr(booking, "due_amount", 0) or 0),
    }
    return ctx





@login_required
def booking_invoice_summary(request, pk: int):
    booking = get_object_or_404(
        Booking.objects.select_related("guest", "room", "room__category"),
        pk=pk
    )
    ctx = _ctx_base(request, booking)
    ctx["page_title"] = "Invoice Summary"
    return render(request, "bookings/invoice_summary.html", ctx)




# apps/bookings/views_invoices.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from web_project import TemplateHelper
from .models import Booking

@login_required
def booking_invoice_summary(request, pk: int):
    booking = get_object_or_404(
        Booking.objects.select_related("guest", "room", "room__category"),
        pk=pk
    )

    # Build context; site_settings will come from your context processor
    ctx = {
        "layout_path": TemplateHelper.set_layout("layout_blank.html", {}),  # print-friendly
        "booking": booking,
        "guest": booking.guest,
        "room": booking.room,
        # snapshot numbers (integers assumed)
        "rate": int(getattr(booking, "nightly_rate", 0) or 0),
        "gross": int(getattr(booking, "gross_amount", 0) or 0),
        "discount": int(getattr(booking, "discount_amount", 0) or 0),
        "net": int(getattr(booking, "net_amount", 0) or 0),
        "paid": int(getattr(booking, "payment_amount", 0) or 0),
        "due": int(getattr(booking, "due_amount", 0) or 0),
    }
    return render(request, "bookings/invoice_summary.html", ctx)
