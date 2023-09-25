from django.shortcuts import render
from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import JsonResponse
from gspread import NoValidUrlKeyFound
from pandas.errors import ParserError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import pandas as pd
import gspread
import hashlib
import os
from django.core.files.storage import FileSystemStorage
import zipfile
import shutil
from datetime import datetime
import warnings

users = [[os.getenv('USER1'), os.getenv('PASSWORD1')]]


class HomeApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                              date_format)).total_seconds() / 60) > 60:
            fs = FileSystemStorage(location=os.path.join(os.getcwd(), 'campus_connect/files/csv_files'))
            for root, dirs, files in os.walk(fs.location):
                for file in files:
                    if f"{request.session['user_name']}" in file:
                        os.remove(os.path.join(root, file))
            request.session.flush()
            return redirect('home')
        if 'logged_in' in request.session and request.session['logged_in']:
            current_datetime = datetime.now()
            # Convert the datetime object to a string
            datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            request.session['last_time'] = datetime_string
            return redirect('campus_connect')
        else:
            return render(request, 'login.html')


class CampusConnectApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                              date_format)).total_seconds() / 60) > 60:
            fs = FileSystemStorage(location=os.path.join(os.getcwd(), 'campus_connect/files/csv_files'))
            for root, dirs, files in os.walk(fs.location):
                for file in files:
                    if f"{request.session['user_name']}" in file:
                        os.remove(os.path.join(root, file))
            request.session.flush()
            return redirect('home')
        elif 'logged_in' in request.session and request.session['logged_in']:
            current_datetime = datetime.now()
            # Convert the datetime object to a string
            datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            request.session['last_time'] = datetime_string
            return render(request, 'home.html')
        else:
            return redirect('home')


class LoginApiView(APIView):
    def get(self, request):
        if 'logged_in' not in request.session:
            user_name = request.GET.get('username')
            password = request.GET.get('password')
            h = hashlib.new("SHA256")
            h.update(user_name.encode())
            hash_name = h.hexdigest()
            h.update(password.encode())
            hash_password = h.hexdigest()
            for user in users:
                if user[0] == hash_name and user[1] == hash_password:
                    current_datetime = datetime.now()
                    # Convert the datetime object to a string
                    datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    request.session['logged_in'] = True
                    request.session['last_time'] = datetime_string
                    request.session['user_name'] = user_name
                    break

            if 'logged_in' in request.session and request.session['logged_in']:
                return redirect('campus_connect')
            else:
                message = 'Please enter correct user name and password!'
                return render(request, 'login.html', {'message': message})
        else:
            return redirect('home')


class LogoutApiView(APIView):
    def get(self, request):
        if 'logged_in' in request.session and request.session['logged_in']:
            fs = FileSystemStorage(location=os.path.join(os.getcwd(), 'campus_connect/files/csv_files'))
            for root, dirs, files in os.walk(fs.location):
                for file in files:
                    if f"{request.session['user_name']}" in file:
                        os.remove(os.path.join(root, file))
            request.session.flush()
        return redirect('home')


