from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'app.views.home', name='home'),
    url(r'^paypal/data.json$', 'app.views.data', name='data'),
    url(r'^paypal$', 'app.views.paypal', name='paypal'),
    url(r'^graphite$', 'app.views.graphite', name='graphite'),
)
