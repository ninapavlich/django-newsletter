from django.conf.urls import patterns, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',

    (r'^grappelli/', include('grappelli.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^newsletter/', include('newsletter.urls')),
)
