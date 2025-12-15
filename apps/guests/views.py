# apps/guests/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from web_project import TemplateLayout, TemplateHelper
from .forms import GuestCreateForm, CompanionFormSet



from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN

@method_decorator(login_required, name="dispatch")
class GuestCreatePage(RequireAnyRoleMixin, TemplateView):
    template_name = "guests/guest_form.html"
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
            "page_title": "Add New Guest",
            "form": GuestCreateForm(),
            "companion_formset": CompanionFormSet(prefix="companions"),
        })

        return context


    def post(self, request, *args, **kwargs):
        form = GuestCreateForm(request.POST, request.FILES)
        formset = CompanionFormSet(request.POST, prefix="companions")

        if form.is_valid() and formset.is_valid():
            guest = form.save(request_user=request.user, auto_create_user=True)
            # bind saved guest to formset, then save companions
            formset.instance = guest
            formset.save()

            messages.success(
                request,
                f"Guest created successfully: {guest.full_name} — stored phone {guest.phone_number}."
            )
            return redirect("list")

        # invalid -> re-render with errors
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
            "page_title": "Add New Guest",
            "form": form,
            "companion_formset": formset,
        })
        return render(request, self.template_name, context)



    # def post(self, request, *args, **kwargs):
    #     form = GuestCreateForm(request.POST, request.FILES)
    #     if form.is_valid():
    #         guest = form.save(request_user=request.user, auto_create_user=True)
    #         messages.success(
    #             request,
    #             f"Guest created successfully: {guest.full_name} — stored phone {guest.phone_number}. "
    #             # "A portal user was created/linked automatically."
    #         )
    #         # ✅ redirect ensures a clean, empty form (new GET request)
    #         return redirect("list")

    #     # If form invalid, re-render with errors and keep filled data
    #     context = TemplateLayout.init(self, super().get_context_data(**kwargs))
    #     context.update({
    #         "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
    #         "page_title": "Add New Guest",
    #         "form": form,
    #     })
    #     return render(request, self.template_name, context)




from django.views.generic import ListView
from django.db.models import Q

from web_project import TemplateLayout, TemplateHelper
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from .models import Guest
from django.utils.dateparse import parse_date

class GuestListPage(RequireAnyRoleMixin, ListView):
    model = Guest
    template_name = "guests/guest_list.html"
    context_object_name = "guests"
    paginate_by = 50
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_queryset(self):
        qs = (
            Guest.objects
            .annotate(companion_count=Count("companions"))  # 👈 add this
            .order_by("-created_at")
        )

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(full_name__icontains=q)
                | Q(phone_number__icontains=q)
                | Q(email__icontains=q)
                | Q(nid_passport__icontains=q)
            )

        profession = self.request.GET.get("profession", "").strip()
        if profession:
            qs = qs.filter(profession__icontains=profession)

        # date range (as you already have)
        start_date_str = self.request.GET.get("start_date", "").strip()
        end_date_str   = self.request.GET.get("end_date", "").strip()
        from django.utils.dateparse import parse_date
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date   = parse_date(end_date_str) if end_date_str else None
        if start_date and end_date:
            qs = qs.filter(created_at__date__range=(start_date, end_date))
        elif start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        elif end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        return qs

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        total_count = context["paginator"].count if "paginator" in context else 0
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
            "page_title": "Guest List",
            "q": self.request.GET.get("q", ""),
            "profession_filter": self.request.GET.get("profession", ""),
            "start_date": self.request.GET.get("start_date", ""),
            "end_date": self.request.GET.get("end_date", ""),
            "total_guests": total_count,
        })
        return context


# class GuestListPage(RequireAnyRoleMixin, ListView):
#     model = Guest
#     template_name = "guests/guest_list.html"
#     context_object_name = "guests"
#     paginate_by = 10
#     allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)



#     def get_queryset(self):
#         qs = Guest.objects.all().order_by("-created_at")
#         q = self.request.GET.get("q", "").strip()
#         if q:
#             qs = qs.filter(
#                 Q(full_name__icontains=q)
#                 | Q(phone_number__icontains=q)
#                 | Q(email__icontains=q)
#                 | Q(nid_passport__icontains=q)
#             )
#         profession = self.request.GET.get("profession", "").strip()
#         if profession:
#             qs = qs.filter(profession__icontains=profession)
#         nationality = self.request.GET.get("nationality", "").strip()
#         if nationality:
#             qs = qs.filter(nationality__icontains=nationality)
#         return qs

#     def get_context_data(self, **kwargs):
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         # count after filters, not just total table
#         total_count = context["paginator"].count if "paginator" in context else 0
#         context.update({
#             "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
#             "page_title": "Guest List",
#             "q": self.request.GET.get("q", ""),
#             "profession_filter": self.request.GET.get("profession", ""),
#             "nationality_filter": self.request.GET.get("nationality", ""),
#             "total_guests": total_count,   # 👈 add this
#         })
#         return context


from django.views.generic import DetailView
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from web_project import TemplateLayout, TemplateHelper
from .models import Guest


# class GuestDetailPage(RequireAnyRoleMixin, DetailView):
#     model = Guest
#     template_name = "guests/guest_detail.html"
#     context_object_name = "guest"
#     allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

#     def get_context_data(self, **kwargs):
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         context.update({
#             "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
#             "page_title": f"Guest Profile — {self.object.full_name}",
#         })
#         return context

from django.db.models import Count

class GuestDetailPage(RequireAnyRoleMixin, DetailView):
    model = Guest
    template_name = "guests/guest_detail.html"
    context_object_name = "guest"
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    # Optimize query: load companions in one go
    def get_queryset(self):
        return (
            Guest.objects
            .prefetch_related("companions")  # GuestCompanion FK
            .select_related("created_by")    # optional
        )

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        guest = self.object
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
            "page_title": f"Guest Profile — {guest.full_name}",
            "companion_count": guest.companions.count(),
        })
        return context


# from django.views.generic import UpdateView
# from django.urls import reverse_lazy

# class GuestEditPage(RequireAnyRoleMixin, UpdateView):
#     model = Guest
#     form_class = GuestCreateForm
#     template_name = "guests/guest_form.html"
#     allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)
#     success_url = reverse_lazy("list")  # redirect to list after update

#     def get_context_data(self, **kwargs):
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         context.update({
#             "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
#             "page_title": f"Edit Guest — {self.object.full_name}",
#         })
#         return context

#     def form_valid(self, form):
#         messages.success(self.request, f"Guest updated successfully: {form.instance.full_name}")
#         return super().form_valid(form)




from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import GuestCreateForm, CompanionFormSet
from .models import Guest
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from web_project import TemplateLayout, TemplateHelper


class GuestEditPage(RequireAnyRoleMixin, UpdateView):
    model = Guest
    form_class = GuestCreateForm
    template_name = "guests/guest_form.html"
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)
    success_url = reverse_lazy("list")  # after save

    # ----- GET -----
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        # if companion_formset already in kwargs (e.g., invalid POST), keep it
        if "companion_formset" not in context:
            context["companion_formset"] = CompanionFormSet(
                instance=self.object, prefix="companions"
            )
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
            "page_title": f"Edit Guest — {self.object.full_name}",
        })
        return context

    # ----- POST (save Guest + Companions together) -----
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()  # GuestCreateForm bound to POST/FILES
        formset = CompanionFormSet(
            request.POST, instance=self.object, prefix="companions"
        )

        if form.is_valid() and formset.is_valid():
            guest = form.save(request_user=request.user, auto_create_user=False)
            formset.instance = guest
            formset.save()
            messages.success(request, f"Guest updated successfully: {guest.full_name}")
            return redirect(self.success_url)

        # invalid -> re-render with errors
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
            "page_title": f"Edit Guest — {self.object.full_name}",
            "form": form,
            "companion_formset": formset,
        })
        return render(request, self.template_name, context)






from django.views import View

class GuestDeleteView(RequireAnyRoleMixin, View):
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def post(self, request, pk):
        try:
            guest = Guest.objects.get(pk=pk)
            guest_name = guest.full_name
            guest.delete()
            messages.success(request, f"Guest '{guest_name}' has been deleted successfully.")
        except Guest.DoesNotExist:
            messages.error(request, "Guest not found or already deleted.")
        return redirect("list")
