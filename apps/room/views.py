from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.views.generic import TemplateView, CreateView, UpdateView
from django.views import View
from django.urls import reverse_lazy

from web_project import TemplateLayout, TemplateHelper
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN

from .models import Room, Category
from .forms import RoomForm, CategoryForm


# ==========================================================
# ROOM + CATEGORY LIST PAGE (Dashboard Table View)
# ==========================================================
@method_decorator(login_required, name="dispatch")
class RoomCategoryListPage(RequireAnyRoleMixin, TemplateView):
    template_name = "room/room_category_list.html"
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Rooms & Categories",
            "rooms": Room.objects.select_related("category").order_by("room_number"),
            "categories": Category.objects.order_by("name"),
        })
        return ctx


# ==========================================================
# CATEGORY CREATE / UPDATE / DELETE
# ==========================================================
@method_decorator(login_required, name="dispatch")
class CategoryCreatePage(RequireAnyRoleMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "room/category_form.html"
    success_url = reverse_lazy("room_list")
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Add Category",
        })
        return ctx

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, f"✅ Category created: {self.object.name or 'Unnamed'}")
        return resp

    def form_invalid(self, form):
        messages.error(self.request, "❌ Failed to create category. Please fix the errors below.")
        return super().form_invalid(form)


@method_decorator(login_required, name="dispatch")
class CategoryUpdatePage(RequireAnyRoleMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "room/category_form.html"
    success_url = reverse_lazy("room_list")
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": f"Edit Category — {self.object.name or 'Unnamed'}",
        })
        return ctx

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, f"✅ Category updated: {self.object.name or 'Unnamed'}")
        return resp

    def form_invalid(self, form):
        messages.error(self.request, "❌ Failed to update category. Please fix the errors below.")
        return super().form_invalid(form)


@method_decorator(login_required, name="dispatch")
class CategoryDeleteView(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def post(self, request, pk):
        try:
            obj = Category.objects.get(pk=pk)
            name = obj.name or "Unnamed"
            obj.delete()
            messages.success(request, f"🗑️ Category '{name}' has been deleted.")
        except Category.DoesNotExist:
            messages.error(request, "⚠️ Category not found or already deleted.")
        return redirect("room_list")


# ==========================================================
# ROOM CREATE / UPDATE / DELETE
# ==========================================================
@method_decorator(login_required, name="dispatch")
class RoomCreatePage(RequireAnyRoleMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = "room/room_form.html"
    success_url = reverse_lazy("room_list")
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Add Room",
        })
        return ctx

    def form_valid(self, form):
        resp = super().form_valid(form)
        title = self.object.name or self.object.room_number or f"#{self.object.pk}"
        messages.success(self.request, f"✅ Room created: {title}")
        return resp

    def form_invalid(self, form):
        messages.error(self.request, "❌ Failed to create room. Please fix the errors below.")
        return super().form_invalid(form)


@method_decorator(login_required, name="dispatch")
class RoomUpdatePage(RequireAnyRoleMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = "room/room_form.html"
    success_url = reverse_lazy("room_list")
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
        title = self.object.name or self.object.room_number or f"Room #{self.object.pk}"
        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": f"Edit Room — {title}",
        })
        return ctx

    def form_valid(self, form):
        resp = super().form_valid(form)
        title = self.object.name or self.object.room_number or f"#{self.object.pk}"
        messages.success(self.request, f"✅ Room updated: {title}")
        return resp

    def form_invalid(self, form):
        messages.error(self.request, "❌ Failed to update room. Please fix the errors below.")
        return super().form_invalid(form)


@method_decorator(login_required, name="dispatch")
class RoomDeleteView(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def post(self, request, pk):
        try:
            obj = Room.objects.get(pk=pk)
            title = obj.name or obj.room_number or f"#{obj.pk}"
            obj.delete()
            messages.success(request, f"🗑️ Room '{title}' has been deleted.")
        except Room.DoesNotExist:
            messages.error(request, "⚠️ Room not found or already deleted.")
        return redirect("room_list")




# apps/room/views.py
from datetime import date, timedelta
from django.utils.dateparse import parse_date
from django.http import JsonResponse
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Min, Max

from web_project import TemplateLayout, TemplateHelper
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN

from apps.room.models import Room
from apps.bookings.models import Booking

# ---- shared helper ----
def _parse_range(request):
    today = date.today()
    cin = parse_date(request.GET.get("in") or "") or today
    cout = parse_date(request.GET.get("out") or "") or (cin + timedelta(days=1))
    if cout <= cin:
        cout = cin + timedelta(days=1)
    return cin, cout

def _room_row(r: Room, cin: date, cout: date):
    qs = Booking.objects.select_related("guest").filter(room_id=r.id, check_in__lt=cout, check_out__gt=cin)
    is_booked = qs.exists()
    booked_from = qs.aggregate(m=Min("check_in"))["m"]
    booked_to   = qs.aggregate(m=Max("check_out"))["m"]
    b0 = qs.order_by("check_in").first()
    next_free = booked_to if is_booked else cin
    return {
        "id": r.id,
        "room": r.room_number,
        "category": getattr(getattr(r, "category", None), "name", ""),
        "rate": int(r.price or 0),
        "is_booked": is_booked,
        "booked_label": (f"{booked_from:%d %b %Y} → {booked_to:%d %b %Y}" if (booked_from and booked_to) else ""),
        "guest": getattr(getattr(b0, "guest", None), "full_name", "") if is_booked else "",
        "next_free": (next_free.strftime("%d %b %Y") if next_free else ""),
    }

# ---- main combined page ----
@method_decorator(login_required, name="dispatch")
class RoomOverviewPage(RequireAnyRoleMixin, TemplateView):
    template_name = "room/room_overview.html"
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
        cin, cout = _parse_range(self.request)
        rooms = Room.objects.select_related("category").order_by("room_number")
        rows = [_room_row(r, cin, cout) for r in rooms[:30]]
        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Room Overview & Calendar",
            "rooms": rooms,
            "cin": cin.strftime("%Y-%m-%d"),
            "cout": cout.strftime("%Y-%m-%d"),
            "initial_rows": rows,
        })
        return ctx



# ---- ajax: table availability ----
@method_decorator(login_required, name="dispatch")
class RoomsAvailabilityAPI(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)
    def get(self, request):
        cin, cout = _parse_range(request)
        q = (request.GET.get("q") or "").strip()
        status = (request.GET.get("status") or "").lower()
        qs = Room.objects.select_related("category").order_by("room_number")
        if q:
            qs = qs.filter(Q(room_number__icontains=q) | Q(category__name__icontains=q))
        rows = [_room_row(r, cin, cout) for r in qs]
        if status in ("available", "booked"):
            rows = [r for r in rows if r["is_booked"] == (status == "booked")]
        return JsonResponse({"results": rows})

# ---- ajax: per-room calendar ----
# from datetime import date, datetime, timedelta
# from django.http import JsonResponse
# from django.utils.decorators import method_decorator
# from django.contrib.auth.decorators import login_required
# from django.views import View
# from django.db.models import Max

# from apps.core.guards import RequireAnyRoleMixin
# from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
# from apps.bookings.models import Booking


@method_decorator(login_required, name="dispatch")
class RoomCalendarAPI(RequireAnyRoleMixin, View):
    """
    GET ?room=<id>&ym=YYYY-MM   -> month view for a room

    Returns:
      {
        "month_start": "YYYY-MM-DD",
        "month_end":   "YYYY-MM-DD",   # first day of next month (exclusive)
        "events": [
          {
            "id": <booking_id>,
            "start": "YYYY-MM-DD",     # check_in (inclusive)
            "end":   "YYYY-MM-DD",     # check_out + 1 day (exclusive) ✅
            "guest": "Full Name",
            "status": "RESERVED|CHECKED_IN|CHECKED_OUT|CANCELLED"
          }, ...
        ],
        "next_free": "YYYY-MM-DD|null" # max(check_out) among overlaps, same as before
      }
    """
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get(self, request):
        rid = request.GET.get("room")
        ym  = (request.GET.get("ym") or "").strip()

        if not rid:
            return JsonResponse({"error": "Missing room"}, status=400)

        # --- Resolve month window ---
        today = date.today()
        try:
            if ym:
                y, m = map(int, ym.split("-"))
            else:
                y, m = today.year, today.month
            month_start = date(y, m, 1)
        except Exception:
            # Fallback to current month on bad ym
            month_start = date(today.year, today.month, 1)

        # First day of next month (exclusive)
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1)

        # --- Bookings that overlap this month window ---
        qs = (Booking.objects
              .select_related("guest")
              .filter(room_id=rid,
                      check_in__lt=month_end,   # overlap
                      check_out__gt=month_start)
              .order_by("check_in", "id"))

        # IMPORTANT: end must be exclusive; use check_out + 1 day
        events = []
        for b in qs:
            events.append({
                "id": b.id,
                "start": b.check_in.isoformat(),
                "end":   (b.check_out + timedelta(days=1)).isoformat(),  # ✅ inclusive rendering
                "guest": b.guest.full_name if b.guest_id else "",
                "status": b.status,
            })

        # keep your "next_free" as the latest check_out among overlaps
        latest_co = qs.aggregate(mx=Max("check_out"))["mx"]
        next_free = latest_co.isoformat() if latest_co else None

        return JsonResponse({
            "month_start": month_start.isoformat(),
            "month_end":   month_end.isoformat(),
            "events":      events,
            "next_free":   next_free,
        })
