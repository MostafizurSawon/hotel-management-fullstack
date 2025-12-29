from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.urls import reverse_lazy

from web_project import TemplateLayout, TemplateHelper
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN

from .models import Booking
from .forms import BookingForm
from apps.room.models import Room

from django.views.generic import CreateView, UpdateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone


# ---------- Create ----------
# @method_decorator(login_required, name="dispatch")
# class BookingCreatePage(RequireAnyRoleMixin, CreateView):
#     model = Booking
#     form_class = BookingForm
#     template_name = "bookings/booking_form.html"
#     success_url = reverse_lazy("booking_list")
#     allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

#     # pass limited/ordered rooms to the form
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["rooms_qs"] = Room.objects.select_related("category").order_by("room_number")
#         return kwargs

#     def get_context_data(self, **kwargs):
#         ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         ctx.update({
#             "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
#             "page_title": "Add Booking",
#             "room_options": [...],
#             "booking_id": None,
#         })
#         return ctx

#     def form_valid(self, form):
#         obj = form.save(commit=False, request_user=self.request.user)
#         obj.save()  # full_clean runs in model.save()
#         messages.success(self.request, "✅ Booking created successfully.")
#         return redirect(self.success_url)

#     def form_invalid(self, form):
#         messages.error(self.request, "❌ Please correct the errors below.")
#         ctx = self.get_context_data(form=form)
#         return render(self.request, self.template_name, ctx)


# @method_decorator(login_required, name="dispatch")
# class BookingCreatePage(RequireAnyRoleMixin, CreateView):
#     model = Booking
#     form_class = BookingForm
#     template_name = "bookings/booking_form.html"
#     success_url = reverse_lazy("booking_list")
#     allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

#     # pass limited/ordered rooms to the form
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["rooms_qs"] = Room.objects.select_related("category").order_by("room_number")
#         return kwargs

#     def get_context_data(self, **kwargs):
#         ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))

#         # ✅ Build proper room_options (id, rate, label) for the template dropdown
#         rooms = Room.objects.select_related("category").order_by("room_number")
#         room_options = [
#             {
#                 "id": r.id,
#                 "rate": int(getattr(r, "price", 0) or 0),  # adjust if your field is named differently
#                 "label": f"{r.room_number} — {getattr(r.category, 'name', '—') or '—'} — {int(getattr(r, 'price', 0) or 0)}",
#             }
#             for r in rooms
#         ]

#         ctx.update({
#             "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
#             "page_title": "Add Booking",
#             "room_options": room_options,   # <-- no literal [...]
#             "booking_id": None,
#         })
#         return ctx

#     def form_valid(self, form):
#         obj = form.save(commit=False, request_user=self.request.user)
#         obj.save()  # full_clean runs in model.save()
#         messages.success(self.request, "✅ Booking created successfully.")
#         return redirect(self.success_url)

#     def form_invalid(self, form):
#         messages.error(self.request, "❌ Please correct the errors below.")
#         ctx = self.get_context_data(form=form)
#         return render(self.request, self.template_name, ctx)





# views.py (or wherever your BookingCreatePage lives)

import logging
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView

from web_project import TemplateLayout, TemplateHelper

from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import (
    ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
)
from apps.room.models import Room
from apps.bookings.models import Booking
from apps.bookings.forms import BookingForm

# ✅ SMS + site meta helpers
from apps.core.sms import send_sms_jbd, normalize_bd_mobile
from apps.core.site_meta import get_hotel_meta

logger = logging.getLogger(__name__)


from apps.core.sms_log import log_sms




@method_decorator(login_required, name="dispatch")
class BookingCreatePage(RequireAnyRoleMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = "bookings/booking_form.html"
    success_url = reverse_lazy("booking_list")
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    # Pass limited/ordered rooms to the form (if your form expects rooms_qs)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["rooms_qs"] = Room.objects.select_related("category").order_by("room_number")
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))

        # Build dropdown options your template expects (id, rate, label)
        rooms = Room.objects.select_related("category").order_by("room_number")
        room_options = [
            {
                "id": r.id,
                "rate": int(getattr(r, "price", 0) or 0),  # adjust if your rate field differs
                "label": f"{r.room_number} — {getattr(r.category, 'name', '—') or '—'} — {int(getattr(r, 'price', 0) or 0)}",
            }
            for r in rooms
        ]

        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Add Booking",
            "room_options": room_options,
            "booking_id": None,
        })
        return ctx

    def form_valid(self, form):
        # 1) Save booking (model.save handles full_clean)
        obj = form.save(commit=False, request_user=self.request.user)
        obj.save()

        # 2) Try to send SMS (non-blocking)
        try:
            guest = getattr(obj, "guest", None)
            mobile = getattr(guest, "phone_number", None)
            m01 = normalize_bd_mobile(mobile)

            if m01:
                hotel_name, _hotel_phone = get_hotel_meta()
                guest_name = (getattr(guest, "full_name", None) or str(guest) or "Guest").strip()

                # Booking facts
                room_no = getattr(getattr(obj, "room", None), "room_number", "Room")
                ci = obj.check_in.strftime("%d %b %Y")
                co = obj.check_out.strftime("%d %b %Y")

                # Money figures (defensive defaults)
                rate     = int(getattr(obj, "nightly_rate", 0) or 0)
                discount = int(getattr(obj, "discount_amount", 0) or 0)
                paid     = int(getattr(obj, "payment_amount", 0) or 0)
                due      = int(getattr(obj, "due_amount", 0) or 0)

                # Compose message
                msg = (
                    f"Welcome to {hotel_name}, {guest_name}.\n"
                    f"Room: {room_no}\n"
                    f"Check-in: {ci}\n"
                    f"Check-out: {co}\n"
                    f"Discount: ৳{discount}\n"
                    f"Rate/Day: ৳{rate}\n"
                    f"Paid: ৳{paid} | Due: ৳{due}\n"
                    f"Thank you."
                )

                resp = send_sms_jbd(m01, msg)
                ok = isinstance(resp, str) and resp.upper().startswith("SENT")

                # ✅ Persist log (so you can always see when it went)
                try:
                    log_sms(to=m01, body=msg, result=str(resp), context="CREATED", booking_id=obj.pk)
                except Exception:
                    # logging failure must not break flow
                    logger.debug("SmsLog save failed for booking_id=%s", obj.pk, exc_info=True)

                if ok:
                    # ts = timezone.now().strftime("%d %b %Y, %I:%M %p")
                    # messages.success(self.request, f"📨 SMS sent to {m01} at {ts}.")
                    ts = timezone.localtime().strftime("%d %b %Y, %I:%M %p")
                    messages.success(self.request, f"📨 SMS sent to {m01} at {ts}.")

                else:
                    messages.warning(self.request, "⚠️ Booking saved, but SMS not sent.")
            else:
                messages.warning(self.request, "⚠️ Booking saved, but no valid guest mobile found.")
        except Exception as e:
            # Never block booking on SMS failure
            messages.warning(self.request, f"⚠️ SMS sending failed. Booking saved. ({e})")
            logger.exception("SMS sending failed for booking_id=%s", obj.pk)

        # 3) Success flash for booking
        messages.success(self.request, "✅ Booking created successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Please correct the errors below.")
        ctx = self.get_context_data(form=form)
        return render(self.request, self.template_name, ctx)





from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.dateparse import parse_date

from web_project import TemplateLayout, TemplateHelper
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN

from .models import Booking
from apps.room.models import Room





from datetime import date as _date
from django.utils.dateparse import parse_date as _parse_date


@method_decorator(login_required, name="dispatch")
class BookingListPage(RequireAnyRoleMixin, ListView):
    model = Booking
    template_name = "bookings/booking_list.html"
    context_object_name = "bookings"
    paginate_by = 25
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def _safe_parse_date(self, v):
        """
        Accepts: str like '2025-10-26', a date/datetime obj, or junk/None.
        Returns: date or None. Never raises.
        """
        if v is None:
            return None
        # If already a date or datetime
        try:
            if hasattr(v, "isoformat") and isinstance(v, _date):
                return v
            if hasattr(v, "date"):  # datetime -> date
                return v.date()
        except Exception:
            pass
        # If it's a string, strip and parse
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            try:
                return _parse_date(s)
            except Exception:
                return None
        # Anything else (e.g., list) -> try to coerce, else None
        try:
            s = str(v).strip()
            return _parse_date(s)
        except Exception:
            return None

    # def get_queryset(self):
    #     r = self.request
    #     q_text = (r.GET.get("q") or "").strip()
    #     room_id = (r.GET.get("room") or "").strip()
    #     status  = (r.GET.get("status") or "").strip()

    #     # ---- SAFE date parsing (no fromisoformat crashes) ----
    #     ci_start = self._safe_parse_date(r.GET.get("ci_start"))
    #     ci_end   = self._safe_parse_date(r.GET.get("ci_end"))
    #     co_start = self._safe_parse_date(r.GET.get("co_start"))
    #     co_end   = self._safe_parse_date(r.GET.get("co_end"))

    #     qs = (
    #         Booking.objects
    #         .select_related("guest", "room", "room__category")
    #         .order_by("-created_at")
    #     )

    #     if q_text:
    #         qs = qs.filter(
    #             Q(guest__full_name__icontains=q_text) |
    #             Q(room__room_number__icontains=q_text) |
    #             Q(room__category__name__icontains=q_text)
    #         )

    #     if room_id:
    #         qs = qs.filter(room_id=room_id)

    #     if status:
    #         qs = qs.filter(status=status)

    #     # Date range filters — works for DateField/DateTimeField
    #     if ci_start:
    #         qs = qs.filter(check_in__gte=ci_start)
    #     if ci_end:
    #         qs = qs.filter(check_in__lte=ci_end)

    #     if co_start:
    #         qs = qs.filter(check_out__gte=co_start)
    #     if co_end:
    #         qs = qs.filter(check_out__lte=co_end)

    #     return qs

    def get_queryset(self):
        r = self.request
        q_text = (r.GET.get("q") or "").strip()
        room_id = (r.GET.get("room") or "").strip()
        status  = (r.GET.get("status") or "").strip()

        # ---- SAFE date parsing ----
        ci_start = self._safe_parse_date(r.GET.get("ci_start"))
        ci_end   = self._safe_parse_date(r.GET.get("ci_end"))
        co_start = self._safe_parse_date(r.GET.get("co_start"))
        co_end   = self._safe_parse_date(r.GET.get("co_end"))

        qs = (
            Booking.objects
            .select_related("guest", "room", "room__category")
            .order_by("-created_at")
        )

        if q_text:
            qs = qs.filter(
                Q(guest__full_name__icontains=q_text) |
                Q(guest__phone_number__icontains=q_text) |
                Q(room__room_number__icontains=q_text) |
                Q(room__category__name__icontains=q_text)
            )

        if room_id:
            qs = qs.filter(room_id=room_id)

        if status:
            qs = qs.filter(status=status)

        # Date range filters
        if ci_start:
            qs = qs.filter(check_in__gte=ci_start)
        if ci_end:
            qs = qs.filter(check_in__lte=ci_end)

        if co_start:
            qs = qs.filter(check_out__gte=co_start)
        if co_end:
            qs = qs.filter(check_out__lte=co_end)

        return qs

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))

        # (unchanged) build status choices + rooms + preserved_qs
        status_choices = []
        try:
            status_choices = list(Booking._meta.get_field("status").choices or [])
        except Exception:
            status_choices = [
                ("RESERVED", "Reserved"),
                ("CHECKED_IN", "Checked In"),
                ("CHECKED_OUT", "Checked Out"),
                ("CANCELLED", "Cancelled"),
            ]

        from apps.room.models import Room
        rooms = Room.objects.select_related("category").order_by("room_number")

        params = self.request.GET.copy()
        params.pop("page", None)
        preserved_qs = params.urlencode()

        r = self.request
        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Booking List",
            "search_query": (r.GET.get("q") or "").strip(),
            "filter_room": r.GET.get("room", ""),
            "filter_status": r.GET.get("status", ""),
            "ci_start": r.GET.get("ci_start", ""),
            "ci_end": r.GET.get("ci_end", ""),
            "co_start": r.GET.get("co_start", ""),
            "co_end": r.GET.get("co_end", ""),
            "rooms": rooms,
            "status_choices": status_choices,
            "preserved_qs": preserved_qs,
        })
        return ctx



import csv
from django.http import HttpResponse
from datetime import date as _date
from django.utils.dateparse import parse_date as _parse_date


def _safe_parse_date(v):
    if v is None:
        return None
    try:
        if hasattr(v, "isoformat") and isinstance(v, _date):
            return v
        if hasattr(v, "date"):
            return v.date()
    except Exception:
        pass
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return _parse_date(s)
        except Exception:
            return None
    try:
        s = str(v).strip()
        return _parse_date(s)
    except Exception:
        return None

@method_decorator(login_required, name="dispatch")
class BookingExportCSVView(RequireAnyRoleMixin, ListView):
    """
    Returns a CSV of filtered bookings (no pagination).
    Reuses the same filters as BookingListPage.
    """
    model = Booking
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    # reuse filter logic
    def get_queryset(self):
        r = self.request
        q_text = (r.GET.get("q") or "").strip()
        room_id = (r.GET.get("room") or "").strip()
        status  = (r.GET.get("status") or "").strip()

        ci_start = _safe_parse_date(r.GET.get("ci_start"))
        ci_end   = _safe_parse_date(r.GET.get("ci_end"))
        co_start = _safe_parse_date(r.GET.get("co_start"))
        co_end   = _safe_parse_date(r.GET.get("co_end"))

        qs = (
            Booking.objects
            .select_related("guest", "room", "room__category")
            .order_by("-created_at")
        )

        if q_text:
            qs = qs.filter(
                Q(guest__full_name__icontains=q_text) |
                Q(room__room_number__icontains=q_text) |
                Q(room__category__name__icontains=q_text)
            )
        if room_id:
            qs = qs.filter(room_id=room_id)
        if status:
            qs = qs.filter(status=status)
        if ci_start:
            qs = qs.filter(check_in__gte=ci_start)
        if ci_end:
            qs = qs.filter(check_in__lte=ci_end)
        if co_start:
            qs = qs.filter(check_out__gte=co_start)
        if co_end:
            qs = qs.filter(check_out__lte=co_end)

        return qs

    def render_to_response(self, context, **response_kwargs):
        qs = context["object_list"]

        # Prepare response
        filename = "bookings_export.csv"
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'

        # Excel-friendly UTF-8 BOM
        resp.write("\ufeff")

        writer = csv.writer(resp)
        writer.writerow([
            "ID", "Guest", "Phone", "Email",
            "Room", "Category",
            "Check In", "Check Out", "Nights",
            "Nightly Rate", "Gross", "Discount", "Net", "Paid", "Due",
            "Status", "Created At"
        ])

        for b in qs:
            guest = b.guest.full_name if b.guest else ""
            phone = getattr(b.guest, "phone_number", "") if b.guest else ""
            email = getattr(b.guest, "email", "") if b.guest else ""
            room_no = b.room.room_number if b.room else ""
            cat = getattr(getattr(b.room, "category", None), "name", "") if b.room else ""

            writer.writerow([
                b.id,
                guest, phone, email,
                room_no, cat,
                b.check_in.isoformat() if b.check_in else "",
                b.check_out.isoformat() if b.check_out else "",
                getattr(b, "nights", "") or "",
                f"{(b.nightly_rate or 0):.2f}",
                f"{(b.gross_amount or 0):.2f}",
                f"{(b.discount_amount or 0):.2f}",
                f"{(b.net_amount or 0):.2f}",
                f"{(b.payment_amount or 0):.2f}",
                f"{(b.due_amount or 0):.2f}",
                b.status or "",
                b.created_at.strftime("%Y-%m-%d %H:%M") if getattr(b, "created_at", None) else "",
            ])

        return resp






from django.views import View
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from .models import Booking


@method_decorator(login_required, name="dispatch")
class BookingDeleteView(RequireAnyRoleMixin, View):
    """Delete booking from list page with same-page alert"""
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def post(self, request, pk):
        try:
            obj = Booking.objects.get(pk=pk)
            guest = obj.guest.full_name if obj.guest else "Unknown guest"
            obj.delete()
            messages.success(request, f"✅ Booking for {guest} deleted successfully.")
        except Booking.DoesNotExist:
            messages.error(request, "❌ Booking not found or already deleted.")
        return redirect(reverse("booking_list"))



from django.views.generic import UpdateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from web_project import TemplateLayout, TemplateHelper
from .forms import BookingForm  # তোমার form এর নাম অনুযায়ী

# ---------- Edit ----------
# @method_decorator(login_required, name="dispatch")
# class BookingEditPage(RequireAnyRoleMixin, UpdateView):
#     model = Booking
#     form_class = BookingForm
#     template_name = "bookings/booking_form.html"
#     success_url = reverse_lazy("booking_list")
#     allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

#     # pass limited/ordered rooms to the form
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["rooms_qs"] = Room.objects.select_related("category").order_by("room_number")
#         return kwargs

#     def get_context_data(self, **kwargs):
#         ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         ctx.update({
#             "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
#             "page_title": f"Edit Booking — {self.object.guest.full_name if self.object.guest else 'Unknown'}",
#             "room_options": [...],
#             "booking_id": self.object.pk,       # 👈 edit-এ বর্তমান id
#         })
#         return ctx

#     def form_valid(self, form):
#         obj = form.save(commit=False, request_user=self.request.user)
#         obj.save()  # model.full_clean() inside save enforces rules
#         messages.success(self.request, "✅ Booking updated successfully.")
#         return redirect(self.success_url)

#     def form_invalid(self, form):
#         messages.error(self.request, "❌ Please correct the errors below.")
#         ctx = self.get_context_data(form=form)
#         return render(self.request, self.template_name, ctx)

@method_decorator(login_required, name="dispatch")
class BookingEditPage(RequireAnyRoleMixin, UpdateView):
    model = Booking
    form_class = BookingForm
    template_name = "bookings/booking_form.html"
    success_url = reverse_lazy("booking_list")
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))

        rooms = self.model._meta.get_field('room').remote_field.model.objects.select_related('category').order_by('room_number')
        room_options = [
            {
                "id": r.id,
                "label": f"{r.room_number} — {getattr(r.category, 'name', '') or '—'} — {r.price or 0}",
                "rate": str(r.price or 0)
            }
            for r in rooms
        ]

        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": f"Edit Booking — {self.object.guest.full_name if self.object and self.object.guest else 'Unknown'}",
            "room_options": room_options,
            "booking_id": self.object.pk,   # 👈 used by JS (?exclude=<id>)
            "is_edit": True,
        })
        return ctx



    def form_valid(self, form):
        form.save()
        messages.success(self.request, "✅ Booking updated successfully.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        # ✅ Rebuild context with TemplateLayout so `layout_path` is present on error
        messages.error(self.request, "❌ Please correct the errors below.")
        ctx = self.get_context_data(form=form)
        return render(self.request, self.template_name, ctx)





# from django.contrib.auth.decorators import login_required
# from django.views.decorators.http import require_POST
# from django.http import JsonResponse
# from django.shortcuts import get_object_or_404
# from django.db import transaction

# from .models import Booking, Payment

# def _fmt_bdt_int(v: int) -> str:
#     # সব মান integer BDT ধরছি
#     return f"৳ {int(v)}"


# @require_POST
# @login_required
# @transaction.atomic
# def checkout_booking(request, pk: int):
#     """
#     Checkout endpoint:
#     - optional payment.amount (BDT int) নেয়
#     - amount > 0 হলে Payment(CHARGE) create করে
#     - শেষে due == 0 হলে status = CHECKED_OUT, নাহলে CHECKED_IN
#     - সবসময় booking-এর ক্যাশ ফিল্ড রিফ্রেশ করে রিটার্ন দেয়
#     """
#     booking = get_object_or_404(Booking, pk=pk)

#     # payload
#     amount_raw = (request.POST.get("amount") or "").strip()
#     method     = (request.POST.get("method") or "CASH").strip()     # optional
#     txn_ref    = (request.POST.get("txn_ref") or "").strip() or None
#     note       = (request.POST.get("note") or "Checkout payment").strip() or None

#     # sanitize amount
#     try:
#         amount = int(amount_raw) if amount_raw else 0
#     except ValueError:
#         return JsonResponse({"ok": False, "errors": {"amount": ["Enter a valid integer amount."]}}, status=400)

#     if amount < 0:
#         return JsonResponse({"ok": False, "errors": {"amount": ["Amount cannot be negative."]}}, status=400)

#     # optional payment create
#     if amount > 0:
#         # ডিউর বেশি নিলে সাথে সাথেই মেসেজ, মডেল ভ্যালিডেশনও থাকবে
#         if amount > booking.due_amount:
#             return JsonResponse({"ok": False, "errors": {"amount": [f"Amount exceeds current due ({_fmt_bdt_int(booking.due_amount)})."]}}, status=400)

#         payment = Payment(
#             booking=booking,
#             kind=Payment.Kind.CHARGE,
#             method=method,
#             amount=amount,
#             txn_ref=txn_ref,
#             note=note,
#             created_by=request.user,
#         )
#         # model-level rules (overpay/refund guard)
#         from django.core.exceptions import ValidationError
#         try:
#             payment.full_clean()
#             payment.save()
#         except ValidationError as e:
#             return JsonResponse({"ok": False, "errors": e.message_dict}, status=400)

#     # refresh caches & decide status
#     booking.refresh_from_db()  # signals থাকলে সেটাও কভার হবে
#     new_status = Booking.Status.CHECKED_OUT if booking.due_amount == 0 else Booking.Status.CHECKED_IN
#     if booking.status != new_status:
#         booking.status = new_status
#         booking.save(update_fields=["status", "updated_at"])

#     return JsonResponse({
#         "ok": True,
#         "booking_id": booking.id,
#         "status": booking.status,
#         "total_paid": booking.payment_amount,      # integer BDT
#         "balance_due": booking.due_amount,         # integer BDT
#         "total_paid_str": _fmt_bdt_int(booking.payment_amount),
#         "balance_due_str": _fmt_bdt_int(booking.due_amount),
#         "checked_out": booking.status == Booking.Status.CHECKED_OUT,
#     })


# views_ajax.py (or your payments/checkout view file)

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Booking, Payment

# 🔔 add these imports
from apps.core.sms import send_sms_jbd, normalize_bd_mobile
from apps.core.site_meta import get_hotel_meta
from django.conf import settings
from datetime import datetime


def _fmt_bdt_int(v: int) -> str:
    # সব মান integer BDT ধরছি
    return f"৳ {int(v)}"

def _fmt_bdt(v: int) -> str:
    # সব মান integer BDT ধরছি
    return f"৳ {int(v)}"

def _compose_payment_sms(booking: Booking, paid_now: int) -> str:
    """
    পেমেন্ট/চেকআউটের পর সংক্ষিপ্ত কনফার্মেশন SMS।
    """
    hotel_name, hotel_phone = get_hotel_meta()

    guest      = getattr(booking, "guest", None)
    guest_name = getattr(guest, "full_name", "") or "Guest"

    room_no = getattr(getattr(booking, "room", None), "room_number", "Room")
    rate    = int(getattr(booking, "nightly_rate", 0) or getattr(getattr(booking, "room", None), "price", 0) or 0)

    ci = booking.check_in.strftime("%d %b %Y")
    co = booking.check_out.strftime("%d %b %Y")

    total_paid = int(getattr(booking, "payment_amount", 0) or 0)
    due        = int(getattr(booking, "due_amount", 0) or 0)

    # যদি settings.SMS_TEMPLATES থাকে, চেষ্টা করবে
    tmpl_map = getattr(settings, "SMS_TEMPLATES", {}) or {}
    ctx = {
        "hotel": hotel_name,
        "phone": hotel_phone or "",
        "guest": guest_name,
        "code": booking.pk,
        "room": room_no,
        "rate": rate,
        "check_in": ci,
        "check_out": co,
        "paid_now": paid_now,
        "total_paid": total_paid,
        "due": due,
    }
    t = (
        tmpl_map.get("PAYMENT") or
        tmpl_map.get("CHECKOUT") or
        "{hotel}: Payment Successful, {guest}!\n"
        "Booking #{code}\n"
        "Room: {room} | Rate: ৳{rate}/night\n"
        "In: {check_in}  Out: {check_out}\n"
        "Paid now: ৳{paid_now}\n"
        "Total paid: ৳{total_paid} | Due: ৳{due}\n"
        "Thank you."
    )
    try:
        return t.format(**ctx)
    except Exception:
        # safest fallback
        return (
            f"Welcome to {hotel_name}, {guest_name}.\n"
            f"Booking #{booking.pk}\n"
            f"Room: {room_no} | Rate: ৳{rate}/night\n"
            f"In: {ci}  Out: {co}\n"
            f"Paid now: ৳{paid_now}\n"
            f"Total paid: ৳{total_paid} | Due: ৳{due}\n"
            f"Thank you."
        )


# @require_POST
# @login_required
# @transaction.atomic
# def checkout_booking(request, pk: int):
#     """
#     Checkout endpoint:
#     - optional payment.amount (BDT int) নেয়
#     - amount > 0 হলে Payment(CHARGE) create করে
#     - শেষে due == 0 হলে status = CHECKED_OUT, নাহলে CHECKED_IN
#     - সবসময় booking-এর ক্যাশ ফিল্ড রিফ্রেশ করে রিটার্ন দেয়
#     - পেমেন্ট/চেকআউট হলে গেস্টকে SMS পাঠানোর চেষ্টা করে (ফেল করলে বুকিং থামে না)
#     """
#     booking = get_object_or_404(Booking, pk=pk)

#     # payload
#     amount_raw = (request.POST.get("amount") or "").strip()
#     method     = (request.POST.get("method") or "CASH").strip()     # optional
#     txn_ref    = (request.POST.get("txn_ref") or "").strip() or None
#     note       = (request.POST.get("note") or "Checkout payment").strip() or None

#     # sanitize amount
#     try:
#         amount = int(amount_raw) if amount_raw else 0
#     except ValueError:
#         return JsonResponse({"ok": False, "errors": {"amount": ["Enter a valid integer amount."]}}, status=400)

#     if amount < 0:
#         return JsonResponse({"ok": False, "errors": {"amount": ["Amount cannot be negative."]}}, status=400)

#     payment_created = False
#     # optional payment create
#     if amount > 0:
#         if amount > booking.due_amount:
#             return JsonResponse({"ok": False, "errors": {"amount": [f"Amount exceeds current due ({_fmt_bdt_int(booking.due_amount)})."]}}, status=400)

#         payment = Payment(
#             booking=booking,
#             kind=Payment.Kind.CHARGE,
#             method=method,
#             amount=amount,
#             txn_ref=txn_ref,
#             note=note,
#             created_by=request.user,
#         )
#         from django.core.exceptions import ValidationError
#         try:
#             payment.full_clean()
#             payment.save()
#             payment_created = True
#         except ValidationError as e:
#             return JsonResponse({"ok": False, "errors": e.message_dict}, status=400)

#     # refresh caches & decide status
#     booking.refresh_from_db()  # signals থাকলে সেটাও কভার হবে
#     new_status = Booking.Status.CHECKED_OUT if booking.due_amount == 0 else Booking.Status.CHECKED_IN
#     status_changed = (booking.status != new_status)
#     if status_changed:
#         booking.status = new_status
#         booking.save(update_fields=["status", "updated_at"])

#     # 📲 Try to send SMS (non-blocking for booking result)
#     sms_result = {"sent": False, "detail": "skipped"}
#     try:
#         guest = getattr(booking, "guest", None)
#         mobile = getattr(guest, "phone_number", None) if guest else None
#         m01 = normalize_bd_mobile(mobile)
#         if m01:
#             # যদি amount==0 তবু checkout হয়েছে/স্টেটাস চেঞ্জ হয়েছে — তবুও রিপোর্টিং SMS পাঠাতে পারি
#             # এখানে আমরা সর্বশেষ পেমেন্ট/স্টেটাস-পরিস্থিতি দেখিয়ে SMS করি
#             msg = _compose_payment_sms(booking, paid_now=int(amount or 0))
#             res = send_sms_jbd(m01, msg)
#             sms_result = {
#                 "sent": str(res).upper().startswith("SENT"),
#                 "detail": str(res),
#             }
#         else:
#             sms_result = {"sent": False, "detail": "invalid_or_missing_mobile"}
#     except Exception as e:
#         sms_result = {"sent": False, "detail": f"error: {e}"}

#     return JsonResponse({
#         "ok": True,
#         "booking_id": booking.id,
#         "status": booking.status,
#         "total_paid": booking.payment_amount,      # integer BDT
#         "balance_due": booking.due_amount,         # integer BDT
#         "total_paid_str": _fmt_bdt_int(booking.payment_amount),
#         "balance_due_str": _fmt_bdt_int(booking.due_amount),
#         "checked_out": booking.status == Booking.Status.CHECKED_OUT,
#         "sms": sms_result,   # <-- UI চাইলে এখানে warning দেখাতে পারো
#     })

@require_POST
@login_required
@transaction.atomic
def checkout_booking(request, pk: int):
    booking = get_object_or_404(Booking, pk=pk)

    amount_raw = (request.POST.get("amount") or "").strip()
    method     = (request.POST.get("method") or "CASH").strip()
    txn_ref    = (request.POST.get("txn_ref") or "").strip() or None
    note       = (request.POST.get("note") or "Checkout payment").strip() or None

    # sanitize amount
    try:
        amount = int(amount_raw) if amount_raw else 0
    except ValueError:
        return JsonResponse(
            {"ok": False,
             "errors": {"amount": ["Enter a valid integer amount."]},
             "flash": {"level": "danger", "message": "Invalid amount. Please enter a whole number."}},
            status=400
        )

    if amount < 0:
        return JsonResponse(
            {"ok": False,
             "errors": {"amount": ["Amount cannot be negative."]},
             "flash": {"level": "danger", "message": "Amount cannot be negative."}},
            status=400
        )

    payment_created = False
    if amount > 0:
        if amount > booking.due_amount:
            return JsonResponse(
                {"ok": False,
                 "errors": {"amount": [f"Amount exceeds current due ({_fmt_bdt_int(booking.due_amount)})."]},
                 "flash": {"level": "warning", "message": f"Amount exceeds due ({_fmt_bdt_int(booking.due_amount)})."}},
                status=400
            )

        payment = Payment(
            booking=booking,
            kind=Payment.Kind.CHARGE,
            method=method,
            amount=amount,
            txn_ref=txn_ref,
            note=note,
            created_by=request.user,
        )
        from django.core.exceptions import ValidationError
        try:
            payment.full_clean()
            payment.save()
            payment_created = True
        except ValidationError as e:
            return JsonResponse(
                {"ok": False, "errors": e.message_dict,
                 "flash": {"level": "danger", "message": "Payment validation failed. Please check the fields."}},
                status=400
            )

    # refresh caches & decide status
    booking.refresh_from_db()
    new_status = Booking.Status.CHECKED_OUT if booking.due_amount == 0 else Booking.Status.CHECKED_IN
    status_changed = (booking.status != new_status)
    if status_changed:
        booking.status = new_status
        booking.save(update_fields=["status", "updated_at"])

    # ---------------------- SMS (enabled) ----------------------
    # শর্ত: payment_created OR status CHECKED_OUT এ পরিবর্তিত
    sms_result = {"sent": False, "detail": "skipped"}
    try:
        should_sms = payment_created or (status_changed and new_status == Booking.Status.CHECKED_OUT)
        if should_sms:
            guest  = getattr(booking, "guest", None)
            mobile = getattr(guest, "phone_number", None) if guest else None
            m01    = normalize_bd_mobile(mobile)

            if m01:
                msg  = _compose_payment_sms(booking, paid_now=int(amount or 0))
                resp = send_sms_jbd(m01, msg)

                ok = False
                if isinstance(resp, str):
                    s = resp.upper()
                    ok = s.startswith("SENT") or s.startswith("OK") or ("SUCCESS" in s)
                elif isinstance(resp, dict):
                    ok = resp.get("ok") is True or str(resp.get("status","")).upper() in {"SENT","OK","SUCCESS"}

                sms_result = {"sent": ok, "detail": str(resp)}

                # ✅ commit হওয়ার পর লগ সেভ (rollback-safe)
                transaction.on_commit(lambda: log_sms(
                    to=m01, body=msg, result=str(resp),
                    context="Payment/Checkout", booking_id=booking.pk, provider="JBDSMS"
                ))
            else:
                sms_result = {"sent": False, "detail": "invalid_or_missing_mobile"}
    except Exception as e:
        sms_result = {"sent": False, "detail": f"error: {e}"}
    # -----------------------------------------------------------

    # Flash message
    if booking.status == Booking.Status.CHECKED_OUT:
        msg_text = "Checked out successfully! ✅"
    elif payment_created:
        msg_text = "Partial payment recorded. ✅"
    else:
        msg_text = "Status updated. ✅"

    return JsonResponse({
        "ok": True,
        "booking_id": booking.id,
        "status": booking.status,
        "total_paid": booking.payment_amount,
        "balance_due": booking.due_amount,
        "total_paid_str": _fmt_bdt(booking.payment_amount),
        "balance_due_str": _fmt_bdt(booking.due_amount),
        "checked_out": booking.status == Booking.Status.CHECKED_OUT,
        "sms": sms_result,
        "flash": {"level": "success", "message": msg_text},
    })





from django.views.generic import DetailView
from web_project import TemplateLayout, TemplateHelper

# @method_decorator(login_required, name="dispatch")
# class BookingDetailPage(RequireAnyRoleMixin, DetailView):
#     model = Booking
#     template_name = "bookings/booking_detail.html"
#     context_object_name = "booking"
#     allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

#     def get_context_data(self, **kwargs):
#         ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         b = self.object
#         ctx.update({
#             "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
#             "page_title": f"Booking Details — {b.guest.full_name if b.guest else 'Unknown Guest'}",
#         })
#         return ctx



from .models import Payment

@method_decorator(login_required, name="dispatch")
class BookingDetailPage(RequireAnyRoleMixin, DetailView):
    model = Booking
    template_name = "bookings/booking_detail.html"
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
        b: Booking = self.object

        payments = (Payment.objects
                    .filter(booking_id=b.id)
                    .select_related("created_by")
                    .order_by("-received_at", "-id"))

        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": f"Booking #{b.id} — {b.guest.full_name if b.guest_id else ''}",
            "payments": payments,
            # handy aggregates (যদি টেমপ্লেটে দরকার হয়)
            "paid_total": b.payment_amount,
            "due_total": b.due_amount,
            "net_total": b.net_amount,
        })
        return ctx
