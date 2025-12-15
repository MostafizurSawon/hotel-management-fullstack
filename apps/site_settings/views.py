from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper
from django.shortcuts import render, redirect, get_object_or_404

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


from functools import wraps
from django.shortcuts import redirect
from django.utils.decorators import method_decorator


from django.contrib import messages
from django.shortcuts import redirect

def admin_role_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or not user.is_staff:
            messages.error(request, "You are not authorized to access this page.")
            return redirect('index')  # অথবা অন্য যেকোনো উপযুক্ত URL name
        return view_func(request, *args, **kwargs)
    return _wrapped_view



from django.shortcuts import render
from django.views import View



# Site settings



from django.views.generic.edit import CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import SiteSettings
from .forms import SiteSettingsForm
from web_project import TemplateLayout, TemplateHelper



# @method_decorator(admin_role_required, name='dispatch')
class SiteSettingsUpdateView(UpdateView):
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'admin/site_settings.html'
    success_url = reverse_lazy('site_settings')

    def get_object(self):
        return SiteSettings.objects.first()  # Assumes a single settings instance

    def form_valid(self, form):
        messages.success(self.request, "সাইট সেটিংস সফলভাবে সংরক্ষণ করা হয়েছে।")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "ত্রুটি হয়েছে! অনুগ্রহ করে সব তথ্য সঠিকভাবে পূরণ করুন।")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)
        context["page_title"] = "সাইট সেটিংস"
        return context
