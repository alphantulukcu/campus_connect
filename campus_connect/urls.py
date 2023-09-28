# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeApiView.as_view(), name='home'),
    path('login', views.LoginApiView.as_view(), name='login'),
    path('register', views.RegisterApiView.as_view(), name='register'),
    path('create-account', views.CreateAccountApiView.as_view(), name='create_account'),
    path('logout', views.LogoutApiView.as_view(), name='logout'),
    path('campus-connect', views.CampusConnectApiView.as_view(), name='campus_connect'),
]