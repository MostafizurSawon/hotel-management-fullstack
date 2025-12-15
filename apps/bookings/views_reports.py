# apps/bookings/views_reports.py
from datetime import date, timedelta, datetime, time

from django.db.models import Sum, Count
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from web_project import TemplateLayout, TemplateHelper

from apps.guests.models import Guest
from apps.room.models import Room
from .models import Booking, Payment

import re

# -----------------------------
# Flexible date parsing helpers
# -----------------------------

# Pattern:  YYYY-MM-DD-N  (মানে base date থেকে N দিন কমাও)
_REL_RE = re.compile(r"^(?P<base>\d{4}-\d{2}-\d{2})-(?P<delta>\d+)$")

def _parse_flexible_date(s: str):
    """
    Accepts:
      - 'YYYY-MM-DD'        -> that date
      - 'YYYY-MM-DD-N'      -> (YYYY-MM-DD) minus N days
      - '' or invalid       -> None
    """
    if not s:
        return None
    s = s.strip()

    # plain date first
    d = parse_date(s)
    if d:
        return d

    # pattern: YYYY-MM-DD-N
    m = _REL_RE.match(s)
    if m:
        base = parse_date(m.group("base"))
        delta = int(m.group("delta") or 0)
        if base:
            return base - timedelta(days=delta)

    return None


def _default_dates(request):
    """
    Returns (df, dt) as date objects.
    Default window: last 7 days including today, if no valid query is given.
    """
    today = date.today()

    df_raw = (request.GET.get("from") or "").strip()
    dt_raw = (request.GET.get("to") or "").strip()

    df = _parse_flexible_date(df_raw)
    dt = _parse_flexible_date(dt_raw)

    if not df and not dt:
        # no inputs -> default last 7 days incl. today
        df = today - timedelta(days=6)
        dt = today
    elif df and not dt:
        dt = today
    elif dt and not df:
        df = dt - timedelta(days=6)

    # final safety
    if df is None:
        df = today - timedelta(days=6)
    if dt is None:
        dt = today

    if df > dt:
        df, dt = dt, df

    return df, dt


def _day_start(d: date) -> datetime:
    return datetime.combine(d, time.min)


def _day_end(d: date) -> datetime:
    return datetime.combine(d, time.max)


def _safe_guest_created_q(date_from, date_to):
    """
    Try commonly used timestamp fields on Guest for 'new registrations'.
    Works for DateField or DateTimeField without using '__date'.
    """
    fields = {f.name for f in Guest._meta.get_fields()}
    for fname in ["created_at", "created", "date_joined", "joined_at", "added_on", "updated_at"]:
        if fname in fields:
            return {f"{fname}__gte": _day_start(date_from), f"{fname}__lte": _day_end(date_to)}
    return {}

# -----------------------------
# Report page
# -----------------------------

@method_decorator(login_required, name="dispatch")
class ReportSummaryPage(RequireAnyRoleMixin, TemplateView):
    template_name = "reports/summary.html"
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        # IMPORTANT: TemplateLayout.init expects a request-like object
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))

        df, dt = _default_dates(self.request)

        # --- Bookings in window ---
        # Business rule: booking belongs to window if its check_in is within [df, dt]
        booking_qs = (
            Booking.objects
            .select_related("guest", "room", "room__category")
            .filter(check_in__gte=df, check_in__lte=dt)
            .order_by("-check_in", "-id")
        )
        # যদি overlap logic চাও: .filter(check_in__lte=dt, check_out__gte=df)

        # --- Payments in window ---
        payment_qs = Payment.objects.filter(
            received_at__gte=_day_start(df),
            received_at__lte=_day_end(dt),
        )

        # KPI aggregates (guard None -> 0)
        total_bookings = booking_qs.count()
        sum_net        = booking_qs.aggregate(s=Sum("net_amount"))["s"] or 0
        sum_discount   = booking_qs.aggregate(s=Sum("discount_amount"))["s"] or 0
        sum_due        = booking_qs.aggregate(s=Sum("due_amount"))["s"] or 0

        sum_received   = payment_qs.aggregate(s=Sum("amount"))["s"] or 0
        total_invoices = payment_qs.count()

        # New guests (defensive on field name & type)
        gf = _safe_guest_created_q(df, dt)
        new_guests = Guest.objects.filter(**gf).count() if gf else 0

        # Per-room rollup
        per_room = (
            booking_qs
            .values("room_id", "room__room_number", "room__category__name")
            .annotate(
                bookings=Count("id"),
                net=Sum("net_amount"),
                received=Sum("payment_amount"),
                due=Sum("due_amount"),
            )
            .order_by("room__room_number")
        )

        rooms = Room.objects.select_related("category").order_by("room_number")

        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Reports — Summary",
            "date_from": df,
            "date_to": dt,
            "rooms": rooms,
            "kpi": {
                "new_guests": int(new_guests),
                "total_bookings": int(total_bookings),
                "total_invoices": int(total_invoices),
                "sum_net": int(sum_net),
                "sum_discount": int(sum_discount),
                "sum_received": int(sum_received),
                "sum_due": int(sum_due),
            },
            "bookings": booking_qs,
            "per_room": per_room,
            "preserved_qs": self.request.GET.urlencode(),
        })
        return ctx
