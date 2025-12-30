from django.views.generic import TemplateView
from web_project import TemplateLayout, TemplateHelper
from apps.room.models import Category

class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(
            self, super().get_context_data(**kwargs)
        )

        context.update({
            "layout_path": TemplateHelper.set_layout(
                "layout_blank.html", context
            ),
            "is_front": True,

            # 🔹 REQUIRED for search form
            "room_categories": Category.objects.all().order_by("name"),
            "searched": False,
        })

        return context
