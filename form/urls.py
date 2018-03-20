from django.urls import path, re_path

from . import views

app_name = 'form'

urlpatterns = [
    # ex: /
    path('', views.home, name='home'),
    # ex: /signup
    path('signup', views.signup, name='signup'),
]