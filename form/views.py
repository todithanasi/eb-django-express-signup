import sys

from boto3.dynamodb.conditions import Key
from django.http import HttpResponse
from collections import Counter
import os
import boto3
import botocore
from django.shortcuts import render
from .models import Leads, Tweets
import vincent
from django.conf import settings

import json
from django.http import JsonResponse
from django.core import serializers
from django.http import JsonResponse

BASE_DIR = getattr(settings, "BASE_DIR", None)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_KEY')



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
    items_to_show = json.dumps(bar.to_json())
    return render(request, 'chart.html', {'items_to_show': items_to_show})


def map(request):
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')
    filename = from_date + '-' + to_date + '.json'
    geo_data = {
        "type": "FeatureCollection",
        "features": []
    }
    bucket_name = 'gsg-maps-dump'
    # connect to s3
    conn = boto3.resource('s3')

    # get s3 bucket
    bucket = conn.Bucket(bucket_name)
    key = filename
    objs = list(bucket.objects.filter(Prefix=key))
    # if file doesn't exist only then create the file
    if len(objs) <= 0:
        tweets = Tweets()
        for tweet in tweets.get_tweets(from_date,to_date):
            geo_json_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [tweet['c0'], tweet['c1']]
                },
                "properties": {
                    "text": tweet['text'],
                    "created_at": tweet['created_at']
                }
            }
            geo_data['features'].append(geo_json_feature)
        conn.Object(bucket_name, filename).put(Body=json.dumps(geo_data, indent=4))
    return render(request, 'map.html', {'filename': filename})