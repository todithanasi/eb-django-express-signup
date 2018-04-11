from django.http import HttpResponse
from collections import Counter
import os
from django.shortcuts import render
from .models import Leads
import vincent
from django.conf import settings

import json
from django.http import JsonResponse
from django.core import serializers

BASE_DIR = getattr(settings, "BASE_DIR", None)


def home(request):
    return render(request, 'index.html')


def signup(request):
    leads = Leads()
    status = leads.insert_lead(request.POST['name'], request.POST['email'], request.POST['previewAccess'])
    if status == 200:
        leads.send_notification(request.POST['email'])
    return HttpResponse('', status=status)



def search(request):
    domain = request.GET.get('domain')
    preview = request.GET.get('preview')
    leads = Leads()
    items = leads.get_leads(domain, preview)
    if domain or preview:
        return render(request, 'search.html', {'items': items})
    else:
        domain_count = Counter()
        domain_count.update([item['email'].split('@')[1] for item in items])
        return render(request, 'search.html', {'domains': sorted(domain_count.items())})

# def chart(request):
#     domain = request.GET.get('domain')
#     preview = request.GET.get('preview')
#     leads = Leads()
#     items = leads.get_leads(domain, preview)
#     domain_count = Counter()
#     domain_count.update([item['email'].split('@')[1] for item in items])
#     domain_freq = domain_count.most_common(15)
#     if len(domain_freq) == 0:
#         return HttpResponse('No items to show', status=200)
#     labels, freq = zip(*domain_freq)
#     data = {'data': freq, 'x': labels}
#     bar = vincent.Bar(data, iter_idx='x')
#     bar.to_json(os.path.join(BASE_DIR, 'static', 'domain_freq.json'))
#     return render(request, 'chart.html', {'items': []})

def chart(request):
    domain = request.GET.get('domain')
    preview = request.GET.get('preview')
    leads = Leads()
    items = leads.get_leads(domain, preview)
    domain_count = Counter()
    domain_count.update([item['email'].split('@')[1] for item in items])
    domain_freq = domain_count.most_common(15)
    if len(domain_freq) == 0:
        return HttpResponse('No items to show', status=200)
    labels, freq = zip(*domain_freq)
    data = {'data': freq, 'x': labels}
    bar = vincent.Bar(data, iter_idx='x')
    items_to_show = bar.to_json()
    # items_to_show = serializers.serialize('json', items_to_show)
    # return JsonResponse(items_to_show, "DjangoJSONEncoder", False)
    return render(request, 'chart.html', {"items_to_show": items_to_show},"application/json")