from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages

from web_project import TemplateLayout, TemplateHelper

from apps.bookings.models import Booking
from apps.bookings.forms import GuestBookingForm
from apps.room.models import Room


class GuestBookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = GuestBookingForm
    template_name = "bookings/guest_booking_form.html"

    # 🔒 Only guest users allowed
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("guest_login")

        if getattr(request.user, "role", None) != "guest":
            messages.error(request, "You are not allowed to access this page.")
            return redirect("index")

        return super().dispatch(request, *args, **kwargs)

    # 🔹 Pass rooms queryset to form
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["rooms_qs"] = Room.objects.select_related("category").order_by("room_number")
        return kwargs

    # 🔹 Pre-fill from Book Now button
    def get_initial(self):
        initial = super().get_initial()

        initial["room"] = self.request.GET.get("room") or None
        initial["check_in"] = self.request.GET.get("check_in") or None
        initial["check_out"] = self.request.GET.get("check_out") or None

        # 🔒 Force pending (never trust frontend)
        initial["status"] = Booking.Status.PENDING

        return initial

    # 🔹 Page context
    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))

        rooms = Room.objects.select_related("category").order_by("room_number")
        room_options = [
            {
                "id": r.id,
                "rate": int(r.price or 0),
                "label": f"{r.room_number} — {r.category.name if r.category else ''} — ৳{int(r.price or 0)}",
            }
            for r in rooms
        ]

        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Request Booking",
            "room_options": room_options,
            "is_guest_mode": True,
            "booking_id": None,
        })
        return ctx

    # 🔹 Save logic (server-side enforcement)
    def form_valid(self, form):
        obj = form.save(commit=False)

        # 🔒 enforce ownership
        obj.guest = self.request.user.guest
        obj.created_by = self.request.user

        # 🔒 enforce pending status
        obj.status = Booking.Status.PENDING

        # 🔒 block guest from injecting money fields
        obj.discount_amount = 0
        obj.payment_amount = 0
        obj.extra_amount = 0

        obj.save()

        messages.success(
            self.request,
            "Your booking request has been submitted and is pending approval."
        )

        return redirect("guest_booking_success")

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return self.render_to_response(self.get_context_data(form=form))
