from django.http import HttpResponse
from django.shortcuts import render
from .models import Leads


def home(request):
    return render(request, 'index.html')


def signup(request):
    leads = Leads()
    status = leads.insert_lead(request.POST['name'], request.POST['email'], request.POST['previewAccess'])
    if status == 200:
        leads.send_notification(request.POST['email'])
    return HttpResponse('', status=status)
