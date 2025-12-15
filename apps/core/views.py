from django.views.generic import TemplateView
from web_project import TemplateLayout, TemplateHelper

class NoAccessPage(TemplateView):
    template_name = "core/no_access.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", context),
            "page_title": "No Access",
        })
        return context
