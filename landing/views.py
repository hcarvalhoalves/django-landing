from django.shortcuts import get_list_or_404, get_object_or_404
from django.views.generic.simple import direct_to_template
from django.contrib.sites.models import Site
from landing.models import Metric

def index(request):
    return direct_to_template(request, 'landing/index.html',
                              {'metrics': get_list_or_404(Metric),
                               'site': Site.objects.get_current()})

def report(request, pk):
    return direct_to_template(request, 'landing/report.html',
                              {'metric': get_object_or_404(Metric, pk=pk),
                               'site': Site.objects.get_current()})
