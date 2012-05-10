from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'app.views.home', name='home'),
    url(r'^paypal/data.json$', 'app.views.data', name='data'),
    url(r'^paypal$', 'app.views.paypal', name='paypal'),
    url(r'^graphite$', 'app.views.graphite', name='graphite'),
    url(r'^ganglia$', 'app.views.ganglia', name='ganglia'),
    url(r'^webapps/sample-manifest.webapp$', 'app.views.webapp_manifest', name='webapp-manifest'),
    url(r'^webapps/sample-image.png$', 'app.views.webapp_image', name='webapp-image'),
)
