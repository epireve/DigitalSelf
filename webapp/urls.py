from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('webapp.views',
    # First check if this maps to a neemi app call
    url(r'', include('neemi.urls')),
    # Webapp Navigation
    url(r'^$', 'index', name='index'),
    url(r'^register/$', 'register', name='register'),
    url(r'^get_data/$', 'get_data', name='get_data'),
    url(r'^search/$', 'search', name='search'),
    url(r'^delete/$', 'delete', name='delete'),
    url(r'^error/$', 'error', name='error'),
    url(r'^get_stats/$', 'get_stats', name='get_stats'),
    url(r'^contextualize/$', 'contextualize', name='contextualize'),
    url(r'^add_fb_photo/$', 'add_fb_photo', name='add_fb_photo'),
    url(r'^add_fb_event/$', 'add_fb_event', name='add_fb_event')

)

urlpatterns += patterns('',
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    #    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)


