from django.http import JsonResponse
from django.views.decorators.http import require_POST
# apps/bookings/views_ajax.py

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
from django.db import transaction

from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import (
    ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
)

from apps.guests.models import Guest
from apps.room.models import Room
from .models import Booking
from .forms import PaymentForm


# ------------------------------------------------------------
# 📏 Inclusive overlap helper
# Rule: date window [cin, cout] (উভয় প্রান্তই inclusive)
# Two closed intervals [a1, a2] & [b1, b2] overlap iff:
#   (a1 <= b2) AND (a2 >= b1)
# আমাদের কেসে a=[existing.check_in, existing.check_out]
#            b=[cin, cout]
# ------------------------------------------------------------
def _overlap_q_inclusive(cin, cout):
    return Q(check_in__lte=cout) & Q(check_out__gte=cin)


# ------------------------------------------------------------
# 🔍 Guest Search
# GET ?q=
# ------------------------------------------------------------
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
                "label": f"{g.full_name} — {g.phone_number or ''}".strip(" —"),
                "name": g.full_name,
                "phone": g.phone_number,
                "email": g.email,
            }
            for g in qs
        ]
        return JsonResponse({"results": data})


# ------------------------------------------------------------
# 🏠 Room Info
# GET ?id=room_id
# ------------------------------------------------------------
@method_decorator(login_required, name="dispatch")
class RoomInfoAPI(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get(self, request):
        rid = request.GET.get("id")
        if not rid:
            return JsonResponse({"error": "Missing room id"}, status=400)
        try:
            r = Room.objects.select_related("category").get(pk=rid)
        except Room.DoesNotExist:
            return JsonResponse({"error": "Room not found"}, status=404)

        data = {
            "id": r.id,
            "room_number": r.room_number,
            "category": getattr(r.category, "name", None),
            "rate": str(r.price or 0),
        }
        return JsonResponse({"room": data})


# ------------------------------------------------------------
# 📅 Single Room Availability
# GET ?room=<id>&in=YYYY-MM-DD&out=YYYY-MM-DD[&exclude=<booking_id>]
# Returns: {"available": bool, "conflicts":[ids]}
# Only RESERVED / CHECKED_IN will block the room.
# ------------------------------------------------------------
# @method_decorator(login_required, name="dispatch")
# class RoomAvailabilityAPI(RequireAnyRoleMixin, View):
#     allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

#     def get(self, request):
#         rid_raw = request.GET.get("room")
#         cin_s = request.GET.get("in")
#         cout_s = request.GET.get("out")
#         exclude_id = request.GET.get("exclude")

#         # validate inputs
#         try:
#             rid = int(rid_raw)
#         except (TypeError, ValueError):
#             return JsonResponse({"error": "invalid_room"}, status=400)

#         cin = parse_date(cin_s) if cin_s else None
#         cout = parse_date(cout_s) if cout_s else None
#         if not (cin and cout) or cin > cout:
#             return JsonResponse({"error": "invalid_dates"}, status=400)

#         qs = (
#             Booking.objects
#             .filter(
#                 room_id=rid,
#                 status__in=[Booking.Status.RESERVED, Booking.Status.CHECKED_IN],
#             )
#             .filter(_overlap_q_inclusive(cin, cout))
#         )
#         if exclude_id:
#             qs = qs.exclude(pk=exclude_id)

#         conflicts = list(qs.values_list("id", flat=True))
#         return JsonResponse({"available": len(conflicts) == 0, "conflicts": conflicts})

from datetime import timedelta
@method_decorator(login_required, name="dispatch")
class RoomAvailabilityAPI(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get(self, request):
        rid_raw   = request.GET.get("room")
        cin_s     = request.GET.get("in")
        cout_s    = request.GET.get("out")
        exclude_id= request.GET.get("exclude")

        # ---- validate inputs ----
        try:
            rid = int(rid_raw)
        except (TypeError, ValueError):
            return JsonResponse({"error": "invalid_room"}, status=400)

        cin  = parse_date(cin_s) if cin_s else None
        cout = parse_date(cout_s) if cout_s else None
        if not (cin and cout):
            return JsonResponse({"error": "invalid_dates"}, status=400)

        # Normalise to half-open: if out <= in, force out = in + 1 day
        if cout <= cin:
            cout = cin + timedelta(days=1)

        # ---- half-open overlap: existing.check_in < requested.out AND existing.check_out > requested.in ----
        qs = (Booking.objects
              .filter(room_id=rid)
              .exclude(status=Booking.Status.CANCELLED)
              .filter(check_in__lt=cout, check_out__gt=cin))


        # If you're editing an existing booking, ignore itself
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)

        conflicts = list(qs.values_list("id", flat=True))
        return JsonResponse({"available": len(conflicts) == 0, "conflicts": conflicts})


# ------------------------------------------------------------
# 🧩 Available Rooms for a Window (dropdown)
# GET ?in=YYYY-MM-DD&out=YYYY-MM-DD[&exclude=<booking_id>]
# Returns: {"results":[{id,label,rate}]}
# Only RESERVED / CHECKED_IN will block the room.
# ------------------------------------------------------------
@method_decorator(login_required, name="dispatch")
class AvailableRoomsAPI(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get(self, request):
        cin_s = request.GET.get("in")
        cout_s = request.GET.get("out")
        exclude_id = request.GET.get("exclude")

        cin = parse_date(cin_s) if cin_s else None
        cout = parse_date(cout_s) if cout_s else None
        if not (cin and cout) or cin > cout:
            return JsonResponse({"ok": False, "error": "invalid_dates"}, status=400)

        busy = (
            Booking.objects
            .filter(status__in=[Booking.Status.RESERVED, Booking.Status.CHECKED_IN])
            # .filter(_overlap_q_inclusive(cin, cout))
            .filter(check_in__lt=cout, check_out__gt=cin)
        )
        if exclude_id:
            busy = busy.exclude(pk=exclude_id)

        busy_room_ids = busy.values_list("room_id", flat=True)

        rooms = (
            Room.objects
            .select_related("category")
            .exclude(id__in=busy_room_ids)
            .order_by("room_number")
        )

        results = [{
            "id": r.id,
            "label": f"{r.room_number} — {getattr(r.category, 'name', '') or '—'} — {int(r.price or 0)}",
            "rate": int(r.price or 0),
        } for r in rooms]

        return JsonResponse({"ok": True, "results": results})


# ------------------------------------------------------------
# 💳 Add Payment (AJAX)
# POST body: PaymentForm fields; URL: /api/bookings/<booking_id>/payments/add/
# Booking totals auto-update via signals; returns fresh totals.
# ------------------------------------------------------------
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

        booking.refresh_from_db()  # ensure updated totals

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
