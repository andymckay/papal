from datetime import timedelta

from django.conf import settings
from django.utils.datastructures import SortedDict
from django.core import serializers
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import Context, Template
from django.views.decorators.csrf import csrf_exempt

from app.forms import PapalForm, PapalDataForm
from app.models import PapalStats

def format_results(end, diff, query):
    data = {}
    for line in query:
        if line['flag'] not in data:
            data[line['flag']] = [0] * diff

        data[line['flag']][(line['date'] - end).days - 1] = line['flag__count']

    return data

def format_dates(end, diff):
    dates = []
    for x in xrange(diff):
        dates.append((end - timedelta(days=x)).strftime('%Y-%m-%d'))
    dates.reverse()
    return "'" + "','".join(dates) + "'"

@csrf_exempt
def paypal(request):
    form = PapalForm(request.POST or None)
    counts = []
    data = {'render': False,
            'form': form,
            'STATIC_URL': settings.STATIC_URL}
    if form.is_valid():
        query = {'server': form.cleaned_data['server']}
        if form.cleaned_data['level']:
            query['level__in'] = form.cleaned_data['level']
        end = form.cleaned_data['end']
        start = form.cleaned_data['start']
        counts = (PapalStats.objects.values('flag', 'date')
                            .filter(**query)
                            .filter(date__gte=start, date__lte=end)
                            .order_by('date').annotate(Count('flag')))

        data.update({'render': True,
                     'counts': counts,
                     'formatted': format_results(end, (end - start).days + 1, counts),
                     'dates': format_dates(end, (end - start).days + 1),
                    })

    return render_to_response('app/paypal.html', data, mimetype='text/html')

def data(request):
    form = PapalDataForm(request.GET)
    response = HttpResponse(mimetype="text/javascript")
    if form.is_valid():
        queryset = PapalStats.objects.filter(**form.cleaned_data)
        json_serializer = serializers.get_serializer("json")()
        json_serializer.serialize(queryset, ensure_ascii=False, stream=response)
        return response
    return response

def home(request):
    return render_to_response('app/home.html', data, mimetype='text/html')

def graphite(request):
    site = request.GET.get('site', 'addons')
    graph = request.GET.get('graph', 'all-responses')
    site_names = {
        'addons': 'Addons',
        'dev': 'Addons Dev',
        'stage': 'Addons Stage',
        'marketplace': 'Marketplace',
        'marketplace-dev': 'Marketplace Dev',
        'apps-preview': 'Apps Preview',
        'apps-preview-dev': 'Apps Preview Dev'
    }
    site_urls = {
        'addons': 'https://addons.mozilla.org',
        'dev': 'https://addons-dev.allizom.org',
        'stage': 'https://addons.allizom.org',
        'marketplace': 'https://marketplace.mozilla.org',
        'marketplace-dev': 'https://marketplace-dev.allizom.org',
        'apps-preview': 'https://apps-preview.mozilla.org',
        'apps-preview-dev': 'https://apps-preview-dev.allizom.org'
    }
    sites = SortedDict({
        'addons': 'addons',
        'dev': 'addons-dev',
        'stage': 'addons-stage',
        'marketplace': 'addons-marketplace',
        'marketplace-dev': 'addons-marketplacedev',
        'apps-preview': 'addons-appspreview',
        'apps-preview-dev': 'addons-appspreviewdev'
    })
    data = {
        'base': 'https://graphite-phx.mozilla.org/render/?width=586&height=308',
        'site_url': site_urls[site],
        'site_urls': site_urls,
        'site_name': site_names[site],
        'site': sites[site],
        'sites': sites,
        'fifteen': 'from=-15minutes&title=15 minutes',
        'hour': 'from=-1hours&title=1 hour',
        'day': 'from=-24hours&title=24 hours',
        'week': 'from=-7days&title=7 days',
        'month': 'from=-30days&title=30 days',
        '3month': 'from=-90days&title=90 days',
        'ns': 'stats.%s' % sites[site]
    }
    _graphs = (
        ['All Responses', ['target=sumSeries({{ ns }}.response.*)&target={{ ns }}.response.200&target={{ ns }}.response.301&target={{ ns }}.response.302&target={{ ns }}.response.403&target={{ ns }}.response.404&target={{ ns }}.response.405&target={{ ns }}.response.500']],
        ['Site performance', ['target=stats.timers.{{ site }}.view.GET.lower&target=stats.timers.{{ site }}.view.GET.mean&target=stats.timers.{{ site }}.view.GET.upper_90']],
        ['Redirects and Errors', ['target={{ ns }}.response.301&target={{ ns }}.response.302&target={{ ns }}.response.304&target={{ ns }}.response.400&target={{ ns }}.response.403&target={{ ns }}.response.404&target={{ ns }}.response.405&target={{ ns }}.response.500&target={{ ns }}.response.503']],
        ['Celery', ['target=sumSeries({{ site }}.celery.tasks.pending.*.*.*)&target=nonNegativeDerivative(sumSeries({{ site }}.celery.tasks.total.*.*.*))&target=nonNegativeDerivative(sumSeries({{ site }}.celery.tasks.failed.*.*.*))']],
        ['Validation', ['target=stats.timers.{{ site }}.devhub.validator.lower&target=stats.timers.{{ site }}.devhub.validator.mean&target=stats.timers.{{ site }}.devhub.validator.upper_90']],
        ['GUID Search', ['target=stats.timers.{{ site }}.view.api.views.guid_search.GET.lower&target=stats.timers.{{ site }}.view.api.views.guid_search.GET.mean&target=stats.timers.{{ site }}.view.api.views.guid_search.GET.upper_90&target=scale(stats.timers.{{ site }}.view.api.views.guid_search.GET.count(0.01)']],
        ['Update', ['target=stats.timers.{{ site }}.services.update.lower&target=stats.timers.{{ site }}.services.update.mean&target=stats.timers.{{ site }}.services.update.upper_90&target=scale(stats.timers.{{ site }}.services.update.count(0.01)']],
        ['Verify', ['target=stats.timers.{{ site }}.services.verify.lower&target=stats.timers.{{ site }}.services.verify.mean&target=stats.timers.{{ site }}.services.verify.upper_90&target=scale(stats.timers.{{ site }}.services.verify.count(0.01)']],
        ['Homepage', ['target=stats.timers.{{ site }}.view.addons.views.home.GET.lower&target=stats.timers.{{ site }}.view.addons.views.home.GET.mean&target=stats.timers.{{ site }}.view.addons.views.home.GET.upper_90&target=scale(stats.timers.{{ site }}.view.addons.views.home.GET.count,0.1)']],
        ['Search', ['target=stats.timers.{{ site }}.view.search.views.search.GET.lower&target=stats.timers.{{ site }}.view.search.views.search.GET.mean&target=stats.timers.{{ site }}.view.search.views.search.GET.upper_90&target=scale(stats.timers.{{ site }}.view.search.views.search.GET.count,0.1)']],
        ['ES Request', ['target=stats.timers.{{ site }}.search.es.took.lower&target=stats.timers.{{ site }}.search.es.took.mean&target=stats.timers.{{ site }}.search.es.took.upper_90&target=scale(stats.timers.{{ site }}.search.es.took.count%2C0.1)']],
        ['Authenticated Responses', ['target=stats.{{ site }}.response.auth.200&target=scale(stats.{{ site }}.response.200%2C0.1)&from=-1hours']],
        ['Marketplace', ['target=stats.timers.{{ site }}.paypal.paykey.retrieval.upper_90']],
        ['Client', ['target=stats.timers.{{ site }}.window.performance.timing.domInteractive.mean'
                    '&target=stats.timers.{{ site }}.window.performance.timing.domInteractive.upper_90'
                    '&target=stats.timers.{{ site }}.window.performance.timing.domComplete.mean'
                    '&target=stats.timers.{{ site }}.window.performance.timing.domComplete.upper_90'
                    '&target=stats.timers.{{ site }}.window.performance.timing.domLoading.mean'
                    '&target=stats.timers.{{ site }}.window.performance.timing.domLoading.upper_90']],
        ['Client Counts', ['target=stats.{{ site }}.window.performance.navigation.redirectCountstats'
                    '&target=stats.{{ site }}.window.performance.navigation.type.back_forward'
                    '&target=stats.{{ site }}.window.performance.navigation.type.navigate'
                    '&target=stats.{{ site }}.window.performance.navigation.type.reload'
                    '&target=stats.{{ site }}.window.performance.navigation.type.reserved']],
        ['Error Counts', ['target=stats.{{ site }}.error.*']],
        ['Validator', ['target={{ site }}.celery.tasks.total.devhub.tasks.validator']]
    )

    graphs = {}
    ctx = Context(data)
    for name, gs in _graphs:
        slug = name.lower().replace(' ', '-')
        graphs[slug] = {
                'name': name, 'slug': slug,
                'url': [str(Template(g).render(ctx)) for g in gs] }

    data['graphs'] = sorted([ (v['slug'], v['name'], v['url']) for v in graphs.values() ])
    data['graph'] = graphs[graph]
    data['defaults'] = {'site': site, 'graph': graph}
    return render_to_response('app/graphite.html', data, mimetype='text/html')

def webapp_manifest(self):
    response = HttpResponse("""
{
 "name": "Steamcube",
 "description": "A simple 2.5D brain teaser block puzzle game. Find out how far can you get before time runs out?",
 "launch_path": "/steamcube/index.php",
 "developer": {
   "name": "Paul Brunt",
   "url": "http://www.glge.org"
 },
 "icons": {
       "128":"/webapps/sample-image.png"
 },
 "installs_allowed_from": [ "*" ]
}
""", content_type = 'application/x-web-app-manifest+json')
    return response

def webapp_image(self):
    response = HttpResponse(open('/home/amckay/papal/title.png', 'rb'), content_type='image/png')
    import time; time.sleep(3);
    return response 

