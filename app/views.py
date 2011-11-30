from datetime import timedelta
import json

from django.conf import settings
from django.core import serializers
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render_to_response
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
def home(request):
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

    return render_to_response('app/index.html', data, mimetype='text/html')

def data(request):
    form = PapalDataForm(request.GET)
    response = HttpResponse(mimetype="text/javascript")
    if form.is_valid():
        queryset = PapalStats.objects.filter(**form.cleaned_data)
        json_serializer = serializers.get_serializer("json")()
        json_serializer.serialize(queryset, ensure_ascii=False, stream=response)
        return response
    return response
