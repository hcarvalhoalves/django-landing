from django.conf.urls.defaults import *

urlpatterns = patterns('landing.views',
    (r'^$', 'index'),
    (r'^report/(\d+)/$', 'report'),
)
