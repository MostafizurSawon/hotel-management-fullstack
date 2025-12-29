from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
import io
from django.contrib.staticfiles import finders
from django.conf import settings

def link_callback(uri, rel):
    result = finders.find(uri.replace(settings.STATIC_URL, ''))
    if result:
        return result
    return uri

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(
        io.BytesIO(html.encode("UTF-8")),
        result,
        link_callback=link_callback  # <-- This line is essential for static file resolution
    )
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
