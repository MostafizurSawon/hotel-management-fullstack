from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to pages/urls.py file for more pages.
"""


class MiscPagesView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        # Update the context
        context.update(
            {
                "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
            }
        )

        return context





# from django import forms
# from django.db.models import Q
# from django.shortcuts import redirect
# from django.utils.decorators import method_decorator
# from django.views.generic import TemplateView, FormView
# from django.contrib import messages
# from django.conf import settings

# from apps.accounts.utils import role_required, send_sms_jbd
# from apps.admissions.models import HscAdmissions, Session

# from django.db.models import IntegerField, CharField, Value, F
# from django.db.models.functions import Cast, Coalesce, NullIf


# @method_decorator(
#     role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
#     name='dispatch'
# )
# class HscStudentSMSSelectView(TemplateView):
#     template_name = "students/hsc_sms_select.html"

#     class FilterForm(forms.Form):
#         GROUP_CHOICES = [
#             ("", "All groups"),
#             ("science", "Science"),
#             ("commerce", "Business Studies"),
#             ("arts", "Humanities"),
#         ]
#         group = forms.ChoiceField(
#             choices=GROUP_CHOICES,
#             required=False,
#             widget=forms.Select(attrs={"class": "form-control"})
#         )
#         search = forms.CharField(
#             required=False,
#             widget=forms.TextInput(attrs={
#                 "class": "form-control",
#                 "placeholder": "Name/Father/Mobile/Roll"
#             })
#         )

#     def _active_session(self, request):
#         sid = request.session.get('active_session_id')
#         if sid:
#             return Session.objects.filter(id=sid).first()
#         return Session.objects.order_by('-id').first()

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)

#         # Vuexy layout
#         ctx["user"] = self.request.user
#         ctx = TemplateLayout.init(self, ctx)
#         ctx["layout"] = "vertical"
#         ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

#         ctx["page_title"] = "HSC Bulk SMS"
#         ctx["page_subtitle"] = "Select students by Session/Group, then proceed to message."
#         ctx["breadcrumbs"] = [
#             {"label": "Dashboard", "url": "/dashboard/"},
#             {"label": "Students", "url": "/dashboard/admitted-students/hsc"},
#             {"label": "HSC Bulk SMS", "active": True},
#         ]

#         form = self.FilterForm(self.request.GET or None)
#         session = self._active_session(self.request)

#         qs = HscAdmissions.objects.all()
#         if session:
#             qs = qs.filter(add_session=session)

#         qs = qs.exclude(add_mobile__isnull=True).exclude(add_mobile='')

#         if form.is_valid():
#             group = form.cleaned_data.get('group')
#             if group:
#                 qs = qs.filter(add_admission_group=group)

#             search = (form.cleaned_data.get('search') or "").strip()
#             if search:
#                 qs = qs.filter(
#                     Q(add_name__icontains=search) |
#                     Q(add_father__icontains=search) |
#                     Q(add_mobile__icontains=search) |
#                     Q(add_class_roll__icontains=search)
#                 )

#         # Safely sort by roll numerically; blanks/nulls go last, then name
#         qs = qs.annotate(
#             roll_text=Cast(F('add_class_roll'), CharField()),        # int -> text
#             roll_null=NullIf(F('roll_text'), Value('')),             # '' -> NULL
#             roll_i=Cast(F('roll_null'), IntegerField()),             # text/NULL -> int/NULL
#             roll_sort=Coalesce(F('roll_i'), Value(2147483647), output_field=IntegerField()),  # NULL -> big number
#         )

#         students = qs.order_by('roll_sort', 'add_name')[:500]

#         ctx.update({
#             "form": form,
#             "session": session,
#             "students": students,
#         })

#         # 👇 Add delivery summary from last send
#         ctx["last_sms"] = self.request.session.pop("sms_last_summary", None)
#         return ctx

#     def post(self, request, *args, **kwargs):
#         ids = request.POST.getlist("ids")
#         request.session['sms_selected_ids'] = ids
#         return redirect("hsc_sms_compose")


# class _SMSMessageForm(forms.Form):
#     message = forms.CharField(
#         label="SMS Text",
#         widget=forms.Textarea(attrs={
#             "class": "form-control",
#             "rows": 4,
#             "placeholder": "Type your SMS…"
#         }),
#         max_length=480,
#         required=True
#     )


# @method_decorator(
#     role_required(['master_admin', 'admin', 'sub_admin', 'teacher']),
#     name='dispatch'
# )
# class HscStudentSMSComposeView(FormView):
#     template_name = "students/hsc_sms_compose.html"
#     form_class = _SMSMessageForm
#     success_url = None

#     def _active_session(self, request):
#         sid = request.session.get('active_session_id')
#         if sid:
#             return Session.objects.filter(id=sid).first()
#         return Session.objects.order_by('-id').first()

#     def _normalize_bd_mobile(self, mobile: str) -> str | None:
#         if not mobile:
#             return None
#         m = str(mobile).strip()
#         m = m.replace('+880', '').replace('880', '')
#         if not m.startswith('0'):
#             m = '0' + m
#         return m if m.isdigit() and len(m) == 11 and m.startswith('01') else None

#     def _get_selected_students(self, request):
#         ids = request.session.get('sms_selected_ids') or []
#         if not ids:
#             return HscAdmissions.objects.none()
#         return HscAdmissions.objects.filter(id__in=ids)

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         ctx["user"] = self.request.user
#         ctx = TemplateLayout.init(self, ctx)
#         ctx["layout"] = "vertical"
#         ctx["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", ctx)

#         ctx["page_title"] = "HSC Bulk SMS — Compose"
#         ctx["page_subtitle"] = "Review recipients and send a single message to all."
#         ctx["breadcrumbs"] = [
#             {"label": "Dashboard", "url": "/dashboard/"},
#             {"label": "Students", "url": "/dashboard/admitted-students/hsc"},
#             {"label": "HSC Bulk SMS — Compose", "active": True},
#         ]

#         session = self._active_session(self.request)
#         students = self._get_selected_students(self.request)
#         ctx["session"] = session
#         ctx["students"] = students[:500]
#         ctx["selected_count"] = students.count()
#         ctx["sms_sender"] = getattr(settings, "JBD_SENDER_ID", "8809617615010")
#         ctx["sms_ready"] = bool(getattr(settings, "JBD_SMS_TOKEN", None))
#         return ctx

#     def form_valid(self, form):
#         students = self._get_selected_students(self.request)
#         if not students.exists():
#             messages.error(self.request, "No recipients selected. Please select students first.")
#             return redirect("hsc_sms_select")

#         api_token = getattr(settings, "JBD_SMS_TOKEN", "")
#         sender_id = getattr(settings, "JBD_SENDER_ID", "8809617615010")
#         if not api_token:
#             messages.error(self.request, "SMS token missing. Set JBD_SMS_TOKEN in settings/.env.")
#             return redirect("hsc_sms_select")

#         message = form.cleaned_data["message"].strip()
#         if not message:
#             messages.error(self.request, "Please type your SMS text.")
#             return redirect("hsc_sms_compose")

#         normalized_mobiles = {}
#         for s in students:
#             mob = self._normalize_bd_mobile(getattr(s, "add_mobile", ""))
#             if mob:
#                 normalized_mobiles[mob] = s.id

#         if not normalized_mobiles:
#             messages.error(self.request, "No valid mobile numbers among selected students.")
#             return redirect("hsc_sms_select")

#         sent, failed, errors = 0, 0, []
#         for mob in normalized_mobiles.keys():
#             try:
#                 mob_api = f"880{mob[1:]}" if mob.startswith("01") else mob
#                 result = send_sms_jbd(mob_api, message, api_token=api_token, sender_id=sender_id)
#                 if str(result).upper().startswith("SENT"):
#                     sent += 1
#                 else:
#                     failed += 1
#                     errors.append(f"{mob} → {result}")
#             except Exception as e:
#                 failed += 1
#                 errors.append(f"{mob} → EXC: {e}")

#         if sent:
#             messages.success(self.request, f"✅ SMS sent to {sent} recipient(s).")
#         if failed:
#             sample = "; ".join(errors[:5])
#             more = f" (and {len(errors)-5} more…)" if len(errors) > 5 else ""
#             messages.warning(self.request, f"⚠️ Failed: {failed}. {sample}{more}")

#         # 👇 Save summary so it can be shown on select page
#         self.request.session['sms_last_summary'] = {
#             "sent": sent,
#             "failed": failed,
#             "sample": errors[:5],
#         }

#         return redirect("hsc_sms_select")
