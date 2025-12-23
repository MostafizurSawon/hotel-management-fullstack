# apps/bookings/views_ajax.py

from datetime import timedelta

from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q

from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import (
    ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
)

from apps.guests.models import Guest
from apps.room.models import Room
from .models import Booking
from .forms import PaymentForm


# -------------------------------------------------------------------
# 🔍 Guest Search (GET ?q=)
# -------------------------------------------------------------------
@method_decorator(login_required, name="dispatch")
class GuestSearchAPI(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get(self, request):
        q = (request.GET.get("q") or "").strip()
        if not q:
            return JsonResponse({"results": []})

        qs = (
            Guest.objects
            .filter(
                Q(full_name__icontains=q) |
                Q(phone_number__icontains=q) |
                Q(email__icontains=q)
            )
            .order_by("full_name")[:10]
        )
        data = [
            {
                "id": g.id,
                "label": f"{g.full_name} — {g.company or 'N/A'} — {g.phone_number or ''}".strip(" —"),
                "name": g.full_name,
                "company": g.company,
                "phone": g.phone_number,
                "email": g.email,
            }
            for g in qs
        ]
        return JsonResponse({"results": data})


# -------------------------------------------------------------------
# 🏠 Room Info (GET ?id=<room_id>)
# -------------------------------------------------------------------
@method_decorator(login_required, name="dispatch")
class RoomInfoAPI(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get(self, request):
        rid = request.GET.get("id")
        if not rid:
            return JsonResponse({"error": "missing_room_id"}, status=400)

        try:
            r = Room.objects.select_related("category").get(pk=rid)
        except Room.DoesNotExist:
            return JsonResponse({"error": "room_not_found"}, status=404)

        # NOTE: আপনার Room model-এ যদি rate/price ভিন্ন হয়, নিচের ফিল্ড নাম মিলিয়ে নিন
        data = {
            "id": r.id,
            "room_number": r.room_number,
            "category": getattr(r.category, "name", None),
            "rate": int(getattr(r, "price", 0) or 0),
        }
        return JsonResponse({"room": data})


# -------------------------------------------------------------------
# 📅 Single Room Availability
# GET ?room=<id>&in=YYYY-MM-DD&out=YYYY-MM-DD[&exclude=<booking_id>]
# half-open overlap: existing.check_in < out AND existing.check_out > in
# CANCELLED বুকিংগুলো availability ব্লক করবে না।
# -------------------------------------------------------------------
@method_decorator(login_required, name="dispatch")
class RoomAvailabilityAPI(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get(self, request):
        rid_raw    = request.GET.get("room")
        cin_s      = request.GET.get("in")
        cout_s     = request.GET.get("out")
        exclude_id = request.GET.get("exclude")

        # validate room
        try:
            rid = int(rid_raw)
        except (TypeError, ValueError):
            return JsonResponse({"error": "invalid_room"}, status=400)

        # parse dates
        cin  = parse_date(cin_s) if cin_s else None
        cout = parse_date(cout_s) if cout_s else None
        if not (cin and cout):
            return JsonResponse({"error": "invalid_dates"}, status=400)

        # same-day/inverted -> normalize to half-open [cin, cin+1)
        if cout <= cin:
            cout = cin + timedelta(days=1)

        qs = (
            Booking.objects
            .filter(room_id=rid)
            .exclude(status=Booking.Status.CANCELLED)
            .filter(check_in__lt=cout, check_out__gt=cin)
        )
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)

        conflicts = list(qs.values_list("id", flat=True))
        return JsonResponse({"available": len(conflicts) == 0, "conflicts": conflicts})


# -------------------------------------------------------------------
# 🧩 Available Rooms for a Window (dropdown)
# GET ?in=YYYY-MM-DD&out=YYYY-MM-DD[&exclude=<booking_id>]
# Policy: only available rooms returned (booked rooms বাদ)
# -------------------------------------------------------------------
# @method_decorator(login_required, name="dispatch")
# class AvailableRoomsAPI(RequireAnyRoleMixin, View):
#     allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

#     def get(self, request):
#         cin_s      = request.GET.get("in")
#         cout_s     = request.GET.get("out")
#         exclude_id = request.GET.get("exclude")

#         cin  = parse_date(cin_s) if cin_s else None
#         cout = parse_date(cout_s) if cout_s else None
#         if not (cin and cout):
#             return JsonResponse({"ok": False, "error": "invalid_dates"}, status=400)

#         if cout <= cin:
#             cout = cin + timedelta(days=1)

#         busy = (
#             Booking.objects
#             .exclude(status=Booking.Status.CANCELLED)
#             .filter(check_in__lt=cout, check_out__gt=cin)
#         )
#         if exclude_id:
#             busy = busy.exclude(pk=exclude_id)

#         busy_room_ids = busy.values_list("room_id", flat=True)

#         rooms = (
#             Room.objects
#             .select_related("category")
#             .exclude(id__in=busy_room_ids)
#             .order_by("room_number")
#         )

#         results = [{
#             "id": r.id,
#             "label": f"{r.room_number} — {getattr(r.category, 'name', '') or '—'} — {int(getattr(r, 'price', 0) or 0)}",
#             "rate": int(getattr(r, 'price', 0) or 0),
#         } for r in rooms]

#         return JsonResponse({"ok": True, "results": results})


# --- Available Rooms (show all; booked => disabled) ---
from datetime import timedelta
# from django.utils.dateparse import parse_date
# from django.http import JsonResponse
# from django.views import View
# from django.utils.decorators import method_decorator
# from django.contrib.auth.decorators import login_required

# from apps.core.guards import RequireAnyRoleMixin
# from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
# from apps.room.models import Room
# from .models import Booking


@method_decorator(login_required, name="dispatch")
class AvailableRoomsAPI(RequireAnyRoleMixin, View):
    """
    GET ?in=YYYY-MM-DD&out=YYYY-MM-DD[&exclude=<booking_id>]
    Returns ALL rooms with a 'disabled' flag.
    Half-open overlap policy: [in, out)
    CANCELLED bookings do not block.
    """
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get(self, request):
        cin_s      = request.GET.get("in")
        cout_s     = request.GET.get("out")
        exclude_id = request.GET.get("exclude")

        cin  = parse_date(cin_s) if cin_s else None
        cout = parse_date(cout_s) if cout_s else None
        if not (cin and cout):
            return JsonResponse({"ok": False, "error": "invalid_dates"}, status=400)

        # normalize: enforce half-open [cin, out)
        if cout <= cin:
            from datetime import timedelta
            cout = cin + timedelta(days=1)

        # Bookings that block the window
        busy_qs = (
            Booking.objects
            .exclude(status=Booking.Status.CANCELLED)
            .filter(check_in__lt=cout, check_out__gt=cin)
        )
        if exclude_id:
            busy_qs = busy_qs.exclude(pk=exclude_id)

        busy_room_ids = set(busy_qs.values_list("room_id", flat=True))

        rooms = (
            Room.objects
            .select_related("category")
            .order_by("room_number")
        )

        results = []
        for r in rooms:
            rate = int(getattr(r, "price", 0) or 0)
            label = f"{r.room_number} — {getattr(r.category, 'name', '') or '—'} — {rate}"
            results.append({
                "id": r.id,
                "label": label,
                "rate": rate,
                "disabled": (r.id in busy_room_ids),
            })

        return JsonResponse({"ok": True, "results": results})

# -------------------------------------------------------------------
# 💳 Add Payment (AJAX)
# POST: PaymentForm fields  |  URL: /api/bookings/<booking_id>/payments/add/
# Booking totals auto-update via signals; returns fresh totals.
# -------------------------------------------------------------------
def _fmt_bdt(amount_bdt: int) -> str:
    return f"৳ {int(amount_bdt)}"

@require_POST
@login_required
@transaction.atomic
def add_payment(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id)
    form = PaymentForm(request.POST, booking=booking)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.created_by = request.user
        payment.save()
        booking.refresh_from_db()

        return JsonResponse({
            "ok": True,
            "payment_id": payment.id,
            "booking_id": booking.id,
            "total_paid": booking.payment_amount,
            "balance_due": booking.due_amount,
            "total_paid_str": _fmt_bdt(booking.payment_amount),
            "balance_due_str": _fmt_bdt(booking.due_amount),
        })

    return JsonResponse({"ok": False, "errors": form.errors}, status=400)
