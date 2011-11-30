from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'app.views.home', name='home'),
    url(r'^data.json$', 'app.views.data', name='data')
)
