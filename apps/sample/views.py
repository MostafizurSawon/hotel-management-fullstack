from web_project import TemplateLayout, TemplateHelper

from django.views.generic import TemplateView, ListView
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to sample/urls.py file for more pages.
"""
from django.db.models import Count
from django.urls import reverse
from urllib.parse import urlencode
from django.db.models import Q

class SampleView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context






# apps/sample/views.py

from datetime import date, timedelta
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDate

from web_project import TemplateLayout, TemplateHelper
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from apps.bookings.models import Booking
from apps.room.models import Room
from apps.guests.models import Guest


class SampleView(TemplateView):
    def get_context_data(self, **kwargs):
        return TemplateLayout.init(self, super().get_context_data(**kwargs))

from collections import defaultdict
import re
from datetime import date, timedelta

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDate

from web_project import TemplateLayout, TemplateHelper
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from apps.bookings.models import Booking
from apps.room.models import Room


@method_decorator(login_required, name="dispatch")
class DashboardOverviewPage(RequireAnyRoleMixin, TemplateView):
    template_name = "dashboard/overview.html"
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))

        today = date.today()
        tomorrow = today + timedelta(days=1)
        week_ago = today - timedelta(days=6)

        # ---- KPIs ----
        total_bookings = Booking.objects.count()
        active_guests = Booking.objects.filter(
            check_in__lte=today, check_out__gt=today
        ).count()
        occupied_room_ids_today = Booking.objects.filter(
            check_in__lte=today, check_out__gt=today
        ).values_list("room_id", flat=True)
        available_rooms = Room.objects.exclude(id__in=occupied_room_ids_today).count()
        total_revenue = Booking.objects.aggregate(total=Sum("payment_amount"))["total"] or 0

        # ---- 7-day booking trend ----
        trend = (
            Booking.objects.filter(created_at__gte=week_ago)
            .annotate(day=TruncDate("created_at"))
            .values("day").annotate(count=Count("id")).order_by("day")
        )
        chart_labels = [t["day"].strftime("%b %d") if t["day"] else "" for t in trend]
        chart_data   = [t["count"] for t in trend]

        # ---- Revenue by Room Category ----
        rev_by_cat = (
            Booking.objects
            .values("room__category__name")
            .annotate(total=Sum("payment_amount"))
            .order_by("room__category__name")
        )
        cat_labels = [r["room__category__name"] or "Uncategorized" for r in rev_by_cat]
        cat_data   = [float(r["total"] or 0) for r in rev_by_cat]

        # ---- Monthly revenue (last 6 months) ----
        six_months_ago = today - timedelta(days=180)
        monthly = (
            Booking.objects.filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth("created_at"))
            .values("month").annotate(total=Sum("payment_amount")).order_by("month")
        )
        month_labels = [m["month"].strftime("%b %Y") if m["month"] else "" for m in monthly]
        month_data   = [float(m["total"] or 0) for m in monthly]

        # ---- Today's lists ----
        todays_checkins = (
            Booking.objects.select_related("guest", "room", "room__category")
            .filter(check_in__gte=today, check_in__lt=tomorrow)
            .order_by("check_in")[:20]
        )
        todays_checkouts = (
            Booking.objects.select_related("guest", "room", "room__category")
            .filter(check_out__gte=today, check_out__lt=tomorrow)
            .order_by("check_out")[:20]
        )

        # ===== Room cards (availability for 'today') =====
        active_bookings = (
            Booking.objects
            .select_related("guest", "room", "room__category")
            .filter(check_in__lte=today, check_out__gt=today)
        )
        active_by_room = {b.room_id: b for b in active_bookings}

        # Helper: get floor from room_number (first digit of first numeric block)
        def room_floor(room_number: str) -> int:
            s = str(room_number or "").strip()
            m = re.search(r"\d+", s)
            if not m:
                return 0
            return int(str(m.group(0))[0])

        # Build floor-wise groups
        floor_groups = defaultdict(list)
        for r in Room.objects.select_related("category").order_by("room_number"):
            active = active_by_room.get(r.id)
            floor = room_floor(r.room_number)
            floor_groups[floor].append({
                "id": r.id,
                "number": r.room_number,
                "category": getattr(r.category, "name", "") or "—",
                "rate": int(r.price or 0),
                "occupied": bool(active),
                "guest": active.guest.full_name if active else "",
                "booking_id": active.id if active else None,
                "ci": active.check_in if active else None,
                "co": active.check_out if active else None,
            })

        # Convert dict -> sorted list for template
        floor_rooms = []
        for fl in sorted(floor_groups.keys()):
            floor_rooms.append({
                "floor": fl if fl != 0 else "—",
                "rooms": sorted(floor_groups[fl], key=lambda x: str(x["number"]))
            })

        # (Optional) flat list if you still use the old block
        room_cards = []
        for block in floor_rooms:
            for r in block["rooms"]:
                room_cards.append({
                    "id": r["id"],
                    "number": r["number"],
                    "category": r["category"],
                    "rate": r["rate"],
                    "occupied": r["occupied"],
                    "guest": r["guest"],
                    "booking_id": r["booking_id"],
                    "ci_str": r["ci"].strftime("%d %b %Y") if r["ci"] else "",
                    "co_str": r["co"].strftime("%d %b %Y") if r["co"] else "",
                })

        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Dashboard Overview",
            "total_bookings": total_bookings,
            "active_guests": active_guests,
            "available_rooms": available_rooms,
            "total_revenue": total_revenue,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
            "cat_labels": cat_labels,
            "cat_data": cat_data,
            "month_labels": month_labels,
            "month_data": month_data,
            "todays_checkins": todays_checkins,
            "todays_checkouts": todays_checkouts,

            # New for floor sections
            "floor_rooms": floor_rooms,
            "room_cards": room_cards,   # if you still render the old grid somewhere
            "today": today,
            "tomorrow": tomorrow,
        })
        return ctx

# ---- Pulse API (with ?d=YYYY-MM-DD) ----
def _selected_day(request) -> date:
    return parse_date(request.GET.get("d") or "") or date.today()

@method_decorator(login_required, name="dispatch")
class DashboardPulseAPI(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get(self, request):
        the_day  = _selected_day(request)
        next_day = the_day + timedelta(days=1)

        total_bookings = Booking.objects.count()

        # occupancy for the selected day
        occupied_qs = Booking.objects.filter(check_in__lte=the_day, check_out__gt=the_day)
        active_guests = occupied_qs.count()

        occupied_room_ids = occupied_qs.values_list("room_id", flat=True)
        available_rooms = Room.objects.exclude(id__in=occupied_room_ids).count()

        total_revenue = float(Booking.objects.aggregate(total=Sum("payment_amount"))["total"] or 0)

        qs_base = Booking.objects.select_related("guest", "room", "room__category")

        ci_qs = qs_base.filter(check_in__gte=the_day, check_in__lt=next_day).order_by("check_in")[:20]
        co_qs = qs_base.filter(check_out__gte=the_day, check_out__lt=next_day).order_by("check_out")[:20]

        def row(b: Booking, is_ci=True):
            return {
                "guest":  b.guest.full_name if b.guest_id else "—",
                "room":   f"{b.room.room_number} ({getattr(getattr(b.room,'category',None),'name','—')})" if b.room_id else "—",
                "time":   (b.check_in if is_ci else b.check_out).strftime("%d %b %Y") if (b.check_in if is_ci else b.check_out) else "",
                "nights": b.nights or "",
            }

        data = {
            "kpi": {
                "total_bookings":  total_bookings,
                "active_guests":   active_guests,
                "available_rooms": available_rooms,
                "total_revenue":   total_revenue,
            },
            "checkins":  [row(b, True)  for b in ci_qs],
            "checkouts": [row(b, False) for b in co_qs],
        }
        return JsonResponse(data)
