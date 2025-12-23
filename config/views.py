# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages

# def home(request):
#     # return redirect('index')
#     return render(request, 'home.html')


from django.views.generic import TemplateView
from web_project import TemplateLayout, TemplateHelper

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
        })

        return context
