import openai
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from datetime import timedelta
from .tokens import account_activation_token
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework.views import APIView
import pandas as pd
import os
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from campus_connect.models import Profile, Post, DonateAd, BorrowAd, Category, Subcategory, Entry, Comment, Chat, Message, Action, Report
import pyrebase
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.views import View
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages


config = {
    "apiKey": os.getenv("API_KEY"),
    "authDomain": os.getenv("AUTH_DOMAIN"),
    "projectId": os.getenv("PROJECT_ID"),
    "storageBucket": os.getenv("STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("MESSAGING_SENDER_ID"),
    "appId": os.getenv("APP_ID"),
    "measurementId": os.getenv("MEASUREMENT_ID"),
    "databaseURL": os.getenv("DATABASE_URL")
}

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()


def error_view(request):
    return render(request, 'error_view.html')


class HomeApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
        except Exception:
            return render(request, 'error_view.html')


class CampusConnectApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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

                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                favorites = list(Action.objects.filter(profile=profile, type='favorite').values_list('post_id', flat=True))
                posts = []
                if len(favorites) > 0:

                    fav_posts = pd.Series(Post.objects.filter(id__in=favorites).values_list('category_id', flat=True))
                    occurrence_counts = fav_posts.value_counts().reset_index()
                    occurrence_counts.columns = ['Element', 'Occurrence Count']
                    top_three_list = occurrence_counts['Element'].tolist()
                    fav_subcategories = Category.objects.filter(id__in=top_three_list).values_list('id', flat=True)

                    posts = Post.objects.filter(category_id__in=fav_subcategories, status=1, is_sold=0).exclude(owner=profile).order_by('-favorites_number')

                if len(posts) == 0:
                    posts = 'Empty'

                now = timezone.now()
                actions = list(Action.objects.filter(profile=profile, type='favorite').values_list('post_id', flat=True))

                return render(request, 'home.html',
                              {'posts': posts, 'now': now, 'actions': actions})
            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class LoginApiView(APIView):
    def post(self, request):
        if 'logged_in' not in request.session:

            user_name = request.POST.get('username')
            password = request.POST.get('password')

            try:
                user = authenticate(username=user_name, password=password)
                if user is not None and user.is_active:
                    current_datetime = datetime.now()
                    # Convert the datetime object to a string
                    datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    request.session['logged_in'] = True
                    request.session['last_time'] = datetime_string
                    request.session['user_name'] = user_name

                    try:
                        profile = Profile.objects.get(user=user)
                    except Exception:
                        profile = Profile.objects.create(user=user,
                                                         created_at=datetime.now())

            except Exception:
                message = 'Please enter correct user name and password!'
                return render(request, 'login.html', {'message': message})

            if 'logged_in' in request.session and request.session['logged_in']:
                return redirect('campus_connect')
            else:
                message = 'Please enter correct user name and password!'
                return render(request, 'login.html', {'message': message})
        else:
            return redirect('home')



class RegisterApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                # Convert the datetime object to a string
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                return render(request, 'login.html')
            else:
                return render(request, 'register.html')
        except Exception:
            return render(request, 'error_view.html')


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        profile, created = Profile.objects.get_or_create(user=user)
        if created:
            profile.created_at = datetime.now()
            profile.save()
        user.save()
        # Redirect to a success page or login page
        return redirect('home')
    else:
        # Token is invalid or expired
        return render(request, 'activation_invalid.html')


def waiting_for_activation(request):
    expiry_time = request.session.get('expiry_time', None)
    return render(request, 'waiting_for_activation.html', {'expiry_time': expiry_time})


class CreateAccountApiView(APIView):
    def post(self, request):
        if 'logged_in' not in request.session:
            user_name = request.POST.get('username')
            user_first_name = request.POST.get('name')
            user_surname = request.POST.get('surname')
            user_email = request.POST.get('email')
            password = request.POST.get('password')
            if 'bilkent.edu.tr' in user_email.split('@')[1]:
                user = User.objects.filter(Q(username=user_name) | Q(email=user_email))
                if user:

                    message = 'Please enter unique username and email!'
                    return render(request, 'register.html', {'message': message})
                else:
                    user = User.objects.create_user(user_name, user_email, password)
                    profile = Profile.objects.create(user=user,
                                                     created_at=datetime.now())

                    # Update fields and then save again
                    user.first_name = user_first_name
                    user.last_name = user_surname

                    user.is_active = False  # User will be activated after email confirmation
                    user.save()

                    expiry_time = datetime.now() + timedelta(minutes=1)
                    request.session['expiry_time'] = expiry_time.strftime("%Y-%m-%d %H:%M:%S")

                    # Generate token
                    token = account_activation_token.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))

                    # activation link
                    activation_link = request.build_absolute_uri(
                        reverse('activate', kwargs={'uidb64': uid, 'token': token})
                    )

                    send_mail(
                        'Activate your account',
                        f'Please click on the link to activate your account: {activation_link}',
                        'dcan474@gmail.com',
                        [user.email],
                        fail_silently=False,
                    )

                    # Redirect to waiting view
                    message = 'An activation link has sent to your email address. '
                    return render(request,'login.html', {'message': message})
            else:
                message = 'Please enter your Bilkent mail!'
                return render(request, 'register.html', {'message': message})

        else:
            return redirect('home')


class LogoutApiView(APIView):
    def get(self, request):
        try:
            if 'logged_in' in request.session and request.session['logged_in']:
                fs = FileSystemStorage(location=os.path.join(os.getcwd(), 'campus_connect/files/csv_files'))
                for root, dirs, files in os.walk(fs.location):
                    for file in files:
                        if f"{request.session['user_name']}" in file:
                            os.remove(os.path.join(root, file))
                request.session.flush()
            return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class ProfileApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)

                posts = Post.objects.filter(owner=profile, status=1, is_sold=0).order_by('-created_at')
                if len(posts) == 0:
                    posts = 'Empty'

                solds = Post.objects.filter(owner=profile, status=1, is_sold=1).order_by('-created_at')
                if len(solds) == 0:
                    solds = 'Empty'

                entries = Entry.objects.filter(owner=profile, status=1).order_by('-created_at')
                if len(entries) == 0:
                    entries = 'Empty'

                now = timezone.now()

                actions = list(Action.objects.filter(profile=profile, type='favorite').values_list('post_id', flat=True))
                favorites = Post.objects.filter(id__in=actions, status=1, is_sold=0)

                likes = list(Action.objects.filter(profile=profile, type='like').values_list('entry_id', flat=True))

                if len(favorites) == 0:
                    favorites = 'Empty'

                return render(request, 'profile_with_posts.html',
                              {'type': 'own', 'profile': profile, 'posts': posts, 'entries': entries, 'now': now, 'actions': actions, 'favorites': favorites, 'likes': likes, 'solds': solds})
            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class SeeAnotherProfileApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string

                user_id = request.POST.get('user_id_1')
                if user_id == '' or user_id is None:
                    user_id = request.POST.get('user_id_2')

                if user_id == '' or user_id is None:
                    user_id = request.POST.get('user_id_3')

                if user_id == '' or user_id is None:
                    user_id = request.POST.get('user_id_4')

                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)

                visited_profile = Profile.objects.get(id=user_id)

                posts = Post.objects.filter(owner=visited_profile, status=1, is_sold=0).order_by('-created_at')
                if len(posts) == 0:
                    posts = 'Empty'

                solds = Post.objects.filter(owner=visited_profile, status=1, is_sold=1).order_by('-created_at')
                if len(solds) == 0:
                    solds = 'Empty'

                entries = Entry.objects.filter(owner=visited_profile, status=1).order_by('-created_at')
                if len(entries) == 0:
                    entries = 'Empty'

                now = timezone.now()

                types = 'visit'
                actions = []
                favorites = []
                if visited_profile.user.username == user.username:
                    types = 'own'
                    actions = list(Action.objects.filter(profile=profile, type='favorite').values_list('post_id', flat=True))
                    favorites = Post.objects.filter(id__in=actions)
                return render(request, 'profile_with_posts.html',
                              {'type': types, 'profile': visited_profile, 'posts': posts, 'entries': entries, 'now': now, 'actions': actions, 'favorites': favorites, 'solds': solds})
            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class EditProfileApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)

                # YAPACAĞINIZ BÜTÜN KOD İŞLEMLERİ BURAYA YAZILACAK !!!!
                # home.html yerine açılmasını istediğiniz sayfanın htmli
                return render(request, 'edit_profile.html', {'profile': profile})  # sadece burda
            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class EditAccountApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                user_name = request.POST.get('edit_username')
                user_first_name = request.POST.get('edit_name')
                user_surname = request.POST.get('edit_surname')
                # user_email = request.POST.get('edit_email')
                user_bio = request.POST.get('edit_bio')
                try:
                    file_input = request.FILES['profile_photo']
                except Exception:
                    file_input = ''

                if user_name != "" and user_name != profile.user.username:
                    try:
                        df_user = pd.DataFrame(User.objects.get(username=user_name))
                        message = 'Please enter unique username or email!'
                        return render(request, 'edit_profile.html', {'message': message})
                    except Exception:
                        user.username = user_name

                if user_first_name != "" and user_first_name != profile.user.first_name:
                    user.first_name = user_first_name

                if user_surname != "" and user_surname != profile.user.last_name:
                    user.last_name = user_surname

                if user_bio != "" and user_bio != profile.bio:
                    profile.bio = user_bio

                if file_input != "":
                    if file_input.name != "" and file_input.name != profile.profile_image:
                        # TOKEN ISSUE
                        # delete_temp_image_path = "gs://facid-6fd44.appspot.com/profilePhotos/" + profile.profile_image
                        # storage.delete(imageURL) # same error happens when URL is passed
                        # storage.delete(delete_temp_image_path)
                        profile.profile_image = file_input.name
                        file_save = default_storage.save(file_input.name, file_input)
                        # token işi böyle sanırsam
                        accessToken = storage.child("profilePhotos/" + file_input.name).put("media/" + file_input.name)
                        profile.profile_image = storage.child("profilePhotos/" + file_input.name).get_url(accessToken)
                        delete = default_storage.delete(file_input.name)
                """
                if user_email != "" and 'bilkent.edu.tr' in user_email.split('@')[1] and user_email != profile.user.email:
                    try:
                        df_user = pd.DataFrame(User.objects.get(Q(username=user_name) | Q(email=user_email)))
                        message = 'Please enter unique username or email!'
                        return render(request, 'edit_profile.html', {'message': message})
        except Exception:
                        profile.user.email = user_email
                        
                """

                user.save()
                profile.save()

                if user_name != request.session['user_name']:
                    request.session['user_name'] = user_name
                return redirect('profile')  # sadece burda
            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class AddApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                categories_post = Category.objects.filter(type=False)
                subcategories = Subcategory.objects.all()
                categories_entry = Category.objects.filter(type=True)

                return render(request, 'add.html',
                              {'profile': profile, 'categories_post': categories_post, 'categories_entry': categories_entry,
                               'subcategories': subcategories})  # sadece burda
            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class AddPostApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                datetime_string_fordb = current_datetime.strftime("%H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                title = request.POST.get('post_title')
                description = request.POST.get('post_description')
                category_id = int(request.POST.get('category'))
                category = Category.objects.get(id=category_id)
                subcategory_id = int(request.POST.get('subcategory'))
                subcategory = Subcategory.objects.get(id=subcategory_id)
                price = request.POST.get('post_price')
                file_input = request.FILES['file_input']
                file_input1 = request.FILES['file_input1']
                file_input2 = request.FILES['file_input2']

                inappropriate_check=contains_inappropriate_content(description)
                inappropriate_check_title=contains_inappropriate_content(title)
                if inappropriate_check or inappropriate_check_title:
                    message = 'Your description/title include inappropriate content(s) to publish!'
                    return render(request, 'add.html', {'message': message,'message_type': 'error','profile': profile})

                urll1 = 'None'
                urll2 = 'None'
                try:

                    file_save = default_storage.save(file_input.name, file_input)
                    token = storage.child("postImages/" + file_input.name).put("media/" + file_input.name)
                    urll = storage.child("postImages/" + file_input.name).get_url(token)
                    delete = default_storage.delete(file_input.name)
                    if file_input1.name != file_input.name:
                        file_save = default_storage.save(file_input1.name, file_input1)
                        token1 = storage.child("postImages/" + file_input1.name).put("media/" + file_input1.name)
                        urll1 = storage.child("postImages/" + file_input1.name).get_url(token1)
                        delete = default_storage.delete(file_input1.name)
                    if file_input2.name != file_input.name:
                        file_save = default_storage.save(file_input2.name, file_input2)
                        token2 = storage.child("postImages/" + file_input2.name).put("media/" + file_input2.name)
                        urll2 = storage.child("postImages/" + file_input2.name).get_url(token2)
                        delete = default_storage.delete(file_input2.name)
                    post = Post.objects.create(owner=profile,
                                               title=title,
                                               description=description,
                                               category=category,
                                               subcategory=subcategory,
                                               price=price,
                                               created_at=datetime.now(),
                                               updated_at=datetime.now(),
                                               post_image=file_input.name,
                                               image_token=urll,
                                               image_token1=urll1,
                                               image_token2=urll2)

                    post.save()
                    user = User.objects.get(username=request.session['user_name'])
                    profile = Profile.objects.get(user=user)

                    posts = Post.objects.filter(owner=profile, status=1, is_sold=0).order_by('-created_at')
                    if len(posts) == 0:
                        posts = 'Empty'

                    solds = Post.objects.filter(owner=profile, status=1, is_sold=1).order_by('-created_at')
                    if len(solds) == 0:
                        solds = 'Empty'

                    entries = Entry.objects.filter(owner=profile, status=1).order_by('-created_at')
                    if len(entries) == 0:
                        entries = 'Empty'

                    now = timezone.now()

                    actions = list(
                        Action.objects.filter(profile=profile, type='favorite').values_list('post_id', flat=True))
                    favorites = Post.objects.filter(id__in=actions)

                    likes = list(Action.objects.filter(profile=profile, type='like').values_list('entry_id', flat=True))

                    if len(favorites) == 0:
                        favorites = 'Empty'
                    message = 'Successfully published.'

                    return render(request, 'profile_with_posts.html',
                                  {'type': 'own', 'profile': profile, 'posts': posts, 'entries': entries, 'now': now,
                                   'actions': actions, 'favorites': favorites, 'likes': likes, 'solds': solds, 'message': message, 'message_type': 'success'})
                except Exception as e:
                    message = 'Something went wrong, please try again!'
                    return render(request, 'add.html', {'message': message,'message_type': 'error', 'profile': profile})

            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class AddEntryApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                title = request.POST.get('entry_title')
                description = request.POST.get('entry_description')
                category_name = int(request.POST.get('category'))
                subcategory_name = int(request.POST.get('subcategory'))
                entry_is_anonymous = request.POST.get('entry_is_anonymous')

                category = Category.objects.get(id=category_name)
                subcategory = Subcategory.objects.get(id=subcategory_name)

                inappropriate_check=contains_inappropriate_content(description)
                inappropriate_check_title=contains_inappropriate_content(title)
                if inappropriate_check or inappropriate_check_title:
                    message = 'Your description/title include inappropriate content(s) to publish!'
                    return render(request, 'add.html', {'message': message,'message_type': 'error','profile': profile})

                if entry_is_anonymous == '0':
                    is_anonymous = False
                else:
                    is_anonymous = True

                try:

                    entry = Entry.objects.create(owner=profile,
                                                 title=title,
                                                 description=description,
                                                 category=category,
                                                 subcategory=subcategory,
                                                 is_anonymous=is_anonymous,
                                                 created_at=datetime.now(),
                                                 updated_at=datetime.now())
                except Exception:
                    message = 'Something went wrong, please try again!'
                    return render(request, 'add.html', {'message': message,'message_type': 'error', 'profile': profile})

                entry.save()
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)

                posts = Post.objects.filter(owner=profile, status=1, is_sold=0).order_by('-created_at')
                if len(posts) == 0:
                    posts = 'Empty'

                solds = Post.objects.filter(owner=profile, status=1, is_sold=1).order_by('-created_at')
                if len(solds) == 0:
                    solds = 'Empty'

                entries = Entry.objects.filter(owner=profile, status=1).order_by('-created_at')
                if len(entries) == 0:
                    entries = 'Empty'

                now = timezone.now()

                actions = list(
                    Action.objects.filter(profile=profile, type='favorite').values_list('post_id', flat=True))
                favorites = Post.objects.filter(id__in=actions)

                likes = list(Action.objects.filter(profile=profile, type='like').values_list('entry_id', flat=True))

                if len(favorites) == 0:
                    favorites = 'Empty'
                message = 'Successfully published.'

                return render(request, 'profile_with_posts.html',
                              {'type': 'own', 'profile': profile, 'posts': posts, 'entries': entries, 'now': now,
                               'actions': actions, 'favorites': favorites, 'likes': likes, 'solds': solds,
                               'message': message, 'message_type': 'success'})
            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class AddDonationApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                datetime_string_fordb = current_datetime.strftime("%H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                title = request.POST.get('donateAd_title')
                description = request.POST.get('donateAd_description')
                file_input = request.FILES['file_input3']
                file_input1 = request.FILES['file_input4']
                file_input2 = request.FILES['file_input5']
                urll1 = 'None'
                urll2 = 'None'
                category_name = int(request.POST.get('category'))
                subcategory_name = int(request.POST.get('subcategory'))
                category = Category.objects.get(id=category_name)
                subcategory = Subcategory.objects.get(id=subcategory_name)
                inappropriate_check=contains_inappropriate_content(description)
                inappropriate_check_title=contains_inappropriate_content(title)
                if inappropriate_check or inappropriate_check_title:
                    message = 'Your description/title include inappropriate content(s) to publish!'
                    return render(request, 'add.html', {'message': message,'message_type': 'error','profile': profile})
                try:

                    file_save = default_storage.save(file_input.name, file_input)
                    token = storage.child("postImages/" + file_input.name).put("media/" + file_input.name)
                    urll = storage.child("postImages/" + file_input.name).get_url(token)
                    delete = default_storage.delete(file_input.name)
                    if file_input1.name != file_input.name:
                        file_save = default_storage.save(file_input1.name, file_input1)
                        token1 = storage.child("postImages/" + file_input1.name).put("media/" + file_input1.name)
                        urll1 = storage.child("postImages/" + file_input1.name).get_url(token1)
                        delete = default_storage.delete(file_input1.name)
                    if file_input2.name != file_input.name:
                        file_save = default_storage.save(file_input2.name, file_input2)
                        token2 = storage.child("postImages/" + file_input2.name).put("media/" + file_input2.name)
                        urll2 = storage.child("postImages/" + file_input2.name).get_url(token2)
                        delete = default_storage.delete(file_input2.name)
                    donate_ad = DonateAd.objects.create(owner=profile,
                                               title=title,
                                               description=description,
                                               category=category,
                                               subcategory=subcategory,
                                               created_at=datetime.now(),
                                               updated_at=datetime.now(),
                                               post_image=file_input.name,
                                               image_token=urll,
                                                image_token1 = urll1,
                                                image_token2=urll2)
                    donate_ad.save()
                    user = User.objects.get(username=request.session['user_name'])
                    profile = Profile.objects.get(user=user)

                    posts = Post.objects.filter(owner=profile, status=1, is_sold=0).order_by('-created_at')
                    if len(posts) == 0:
                        posts = 'Empty'

                    solds = Post.objects.filter(owner=profile, status=1, is_sold=1).order_by('-created_at')
                    if len(solds) == 0:
                        solds = 'Empty'

                    entries = Entry.objects.filter(owner=profile, status=1).order_by('-created_at')
                    if len(entries) == 0:
                        entries = 'Empty'

                    now = timezone.now()

                    actions = list(
                        Action.objects.filter(profile=profile, type='favorite').values_list('post_id', flat=True))
                    favorites = Post.objects.filter(id__in=actions)

                    likes = list(Action.objects.filter(profile=profile, type='like').values_list('entry_id', flat=True))

                    if len(favorites) == 0:
                        favorites = 'Empty'
                    message = 'Successfully published.'

                    return render(request, 'profile_with_posts.html',
                                  {'type': 'own', 'profile': profile, 'posts': posts, 'entries': entries, 'now': now,
                                   'actions': actions, 'favorites': favorites, 'likes': likes, 'solds': solds, 'message': message, 'message_type': 'success'})
                except Exception:
                    message = 'Something went wrong, please try again!'
                    return render(request, 'add.html',
                                  {'message': message, 'message_type': 'error', 'profile': profile})

            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class AddBorrowAdApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                datetime_string_fordb = current_datetime.strftime("%H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                title = request.POST.get('borrowAd_title')
                description = request.POST.get('borrowAd_description')
                category_name = int(request.POST.get('category'))
                subcategory_name = int(request.POST.get('subcategory'))
                price = request.POST.get('borrowAd_price')
                return_day = request.POST.get('borrowAd_return_day')
                file_input = request.FILES['file_input6']
                file_input1 = request.FILES['file_input7']
                file_input2 = request.FILES['file_input8']
                urll1 = 'None'
                urll2 = 'None'

                category = Category.objects.get(id=category_name)
                subcategory = Subcategory.objects.get(id=subcategory_name)

                inappropriate_check=contains_inappropriate_content(description)
                inappropriate_check_title=contains_inappropriate_content(title)
                if inappropriate_check or inappropriate_check_title:
                    message = 'Your description/title include inappropriate content(s) to publish!'
                    return render(request, 'add.html', {'message': message,'message_type': 'error','profile': profile})

                try:

                    file_save = default_storage.save(file_input.name, file_input)
                    token = storage.child("postImages/" + file_input.name).put("media/" + file_input.name)
                    urll = storage.child("postImages/" + file_input.name).get_url(token)
                    delete = default_storage.delete(file_input.name)
                    if file_input1.name != file_input.name:
                        file_save = default_storage.save(file_input1.name, file_input1)
                        token1 = storage.child("postImages/" + file_input1.name).put("media/" + file_input1.name)
                        urll1 = storage.child("postImages/" + file_input1.name).get_url(token1)
                        delete = default_storage.delete(file_input1.name)
                    if file_input2.name != file_input.name:
                        file_save = default_storage.save(file_input2.name, file_input2)
                        token2 = storage.child("postImages/" + file_input2.name).put("media/" + file_input2.name)
                        urll2 = storage.child("postImages/" + file_input2.name).get_url(token2)
                        delete = default_storage.delete(file_input2.name)
                    borrow_ad = BorrowAd.objects.create(owner=profile,
                                               title=title,
                                               description=description,
                                               category=category,
                                               subcategory=subcategory,
                                               price=price,
                                               created_at=datetime.now(),
                                               updated_at=datetime.now(),
                                               post_image=file_input.name,
                                               image_token=urll,
                                               borrow_day=return_day,
                                                image_token1 = urll1,
                                                image_token2=urll2)
                    borrow_ad.save()
                    user = User.objects.get(username=request.session['user_name'])
                    profile = Profile.objects.get(user=user)

                    posts = Post.objects.filter(owner=profile, status=1, is_sold=0).order_by('-created_at')
                    if len(posts) == 0:
                        posts = 'Empty'

                    solds = Post.objects.filter(owner=profile, status=1, is_sold=1).order_by('-created_at')
                    if len(solds) == 0:
                        solds = 'Empty'

                    entries = Entry.objects.filter(owner=profile, status=1).order_by('-created_at')
                    if len(entries) == 0:
                        entries = 'Empty'

                    now = timezone.now()

                    actions = list(
                        Action.objects.filter(profile=profile, type='favorite').values_list('post_id', flat=True))
                    favorites = Post.objects.filter(id__in=actions)

                    likes = list(Action.objects.filter(profile=profile, type='like').values_list('entry_id', flat=True))

                    if len(favorites) == 0:
                        favorites = 'Empty'
                    message = 'Successfully published.'

                    return render(request, 'profile_with_posts.html',
                                  {'type': 'own', 'profile': profile, 'posts': posts, 'entries': entries, 'now': now,
                                   'actions': actions, 'favorites': favorites, 'likes': likes, 'solds': solds, 'message': message, 'message_type': 'success'})
                except Exception as e:
                    message = 'Something went wrong, please try again!'
                    return render(request, 'add.html',
                                  {'message': message, 'message_type': 'error', 'profile': profile})

            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class AddCommentApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:
                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)

                comment = request.POST.get('comment')
                entry_id = request.POST.get('entry_id')

                entries = Entry.objects.filter(id=entry_id)
                now = timezone.now()

                try:
                    comment = Comment.objects.create(owner=profile,
                                                     entry=entries[0],
                                                     comment=comment)
                    comment.save()
                except Exception:
                    message = 'Something went wrong, please try again!'
                    return render(request, 'detailed_post.html', {'type': 'entry', 'entries': entries, 'now': now,
                                                                  'comments': Comment.objects.filter(entry=entries[0])})

                return render(request, 'detailed_post.html', {'type': 'entry', 'entries': entries, 'now': now,
                                                              'comments': Comment.objects.filter(entry=entries[0])})

            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class MarketApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                category = request.GET.get('post_categories')
                subcategory = request.GET.get('post_subcategories')
                post_type = request.GET.get('post_type')
                sort = request.GET.get('sort')
                if post_type != '' and post_type is not None:
                    post_type = post_type[0].lower() + post_type[1:].replace('A', '_a').lower()

                posts = Post.objects.filter(status=1, is_sold=0)
                try:
                    if category != '' or category is not None:
                        category = Category.objects.get(name=category)
                        if subcategory != '' and subcategory is not None:
                            subcategory = Subcategory.objects.get(name=subcategory)
                            if post_type != '' and post_type is not None:
                                posts = Post.objects.filter(category=category, subcategory=subcategory, type=post_type, status=1, is_sold=0) #TODO
                            else:
                                posts = Post.objects.filter(category=category, subcategory=subcategory, status=1, is_sold=0) #TODO

                        else:
                            if post_type != '' and post_type is not None:
                                posts = Post.objects.filter(category=category, type=post_type, status=1, is_sold=0)  # TODO
                            else:
                                posts = Post.objects.filter(category=category, status=1, is_sold=0)
                    else:
                        if post_type != '' and post_type is not None:
                            posts = Post.objects.filter(type=post_type, status=1, is_sold=0) # TODO


                except Exception:
                    if post_type != '' and post_type is not None:
                        posts = Post.objects.filter(type=post_type, status=1, is_sold=0)  # TODO
                    else:
                        posts = Post.objects.filter(status=1, is_sold=0) #TODO

                if sort != '' and sort is not None:
                    posts = posts.order_by(sort)
                else:
                    posts = posts.order_by('-created_at')

                if len(posts) == 0:
                    posts = 'Empty'

                now = timezone.now()

                categories = Category.objects.filter(type=0)
                subcategories = Subcategory.objects.all()
                types = ['PostAd', 'BorrowAd', 'DonateAd']
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                actions = list(Action.objects.filter(profile=profile, type='favorite').values_list('post_id', flat=True))

                return render(request, 'market.html',
                              {'posts': posts, 'now': now, 'categories': categories, 'subcategories': subcategories, 'types': types, 'actions': actions})
        except Exception:
            return render(request, 'error_view.html')
        else:
            return redirect('home')  # sadece burda


class ForumApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
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
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                category = request.GET.get('entry_categories')
                subcategory = request.GET.get('entry_subcategories')
                entry_type = request.GET.get('entry_type')
                entries = Entry.objects.filter(status=1).order_by('-created_at')
                verified = list(Profile.objects.filter(is_verified=1).values_list('id', flat=True))
                try:
                    if category != '' or category is not None:
                        category = Category.objects.get(name=category)
                        if subcategory != '' and subcategory is not None:
                            subcategory = Subcategory.objects.get(name=subcategory)
                            if entry_type == 'verified':
                                entries = Entry.objects.filter(category=category, subcategory=subcategory, owner__in=verified, status=1).order_by('-created_at') #TODO
                            else:
                                entries = Entry.objects.filter(category=category, subcategory=subcategory, status=1).order_by('-created_at') #TODO

                        else:
                            if entry_type == 'verified':
                                entries = Entry.objects.filter(category=category, owner__in=verified, status=1).order_by('-created_at')  # TODO
                            else:
                                entries = Entry.objects.filter(category=category, status=1).order_by('-created_at')
                    else:
                        if entry_type == 'verified':
                            entries = Entry.objects.filter(owner__in=verified, status=1).order_by('-created_at')  # TODO


                except Exception:
                    if entry_type == 'verified':

                        entries = Entry.objects.filter(owner__in=verified, status=1).order_by('-created_at')  # TODO
                    else:
                        entries = Entry.objects.filter(status=1).order_by('-created_at') #TODO

                if len(entries) == 0:
                    entries = 'Empty'

                now = timezone.now()
                categories = Category.objects.filter(type=1)
                subcategories = Subcategory.objects.all()
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                actions = list(Action.objects.filter(profile=profile, type='like').values_list('entry_id', flat=True))

                return render(request, 'forum.html', {'entries': entries, 'now': now, 'categories': categories, 'subcategories': subcategories, 'actions': actions})  # sadece burda
            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class ShowPostApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                post_id = request.POST.get('post_id')
                entry_id = request.POST.get('entry_id')
                type = request.POST.get('type')
                if type == 'post':
                    posts = Post.objects.filter(id=post_id)

                    if len(posts) == 0:
                        posts = 'Empty'

                    now = timezone.now()
                    chats = list(Chat.objects.filter(post=posts[0]).values_list('client', flat=True))
                    clients = Profile.objects.filter(id__in=chats)
                    categories = Category.objects.filter(type=0)
                    subcategories = Subcategory.objects.all()

                    return render(request, 'detailed_post.html',
                                  {'profile': profile, 'type': type, 'posts': posts, 'now': now, 'categories': categories,
                                   'subcategories': subcategories, 'clients': clients})

                elif type == 'entry':
                    entries = Entry.objects.filter(id=entry_id)

                    if len(entries) == 0:
                        entries = 'Empty'

                    now = timezone.now()

                    categories = Category.objects.filter(type=1)
                    subcategories = Subcategory.objects.all()
                    comments = Comment.objects.filter(entry=entries[0])

                    return render(request, 'detailed_post.html',
                                  {'type': type, 'entries': entries, 'now': now, 'comments': comments,
                                   'categories': categories, 'subcategories': subcategories})

            else:
                return redirect('home')  # sadece burda
        except Exception:
            return render(request, 'error_view.html')


class DeletePostApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                post_id = request.POST.get('post_id')
                entry_id = request.POST.get('entry_id')
                type = request.POST.get('type')
                if type == 'post':
                    post = Post.objects.get(id=post_id)
                    post.status = 0
                    post.save()
                    now = timezone.now()

                    categories = Category.objects.filter(type=0)
                    subcategories = Subcategory.objects.all()

                    return redirect('profile')

            else:
                return redirect('home')  # sadece burda
        except Exception:
            return render(request, 'error_view.html')


class SoldPostApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                post_id = request.POST.get('post_id')
                client_id = request.POST.get('client_id')
                type = request.POST.get('type')
                if type == 'post':
                    try:
                        post = Post.objects.get(id=post_id)
                        post.is_sold = 1
                        post.save()
                        now = timezone.now()
                        client = Profile.objects.get(id__in=client_id)
                        operation = 'sold'
                        action = Action.objects.create(post=post, profile=client, type=operation)
                        action.save()
                        return redirect('profile')
                    except Exception:
                        return redirect('profile')


            else:
                return redirect('home')  # sadece burda
        except Exception:
            return render(request, 'error_view.html')


class ReportApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                post_id = request.POST.get('post_id')
                entry_id = request.POST.get('entry_id')
                type = request.POST.get('type')
                report_text = request.POST.get('report_text')
                if type == 'post':
                    try:
                        post = Post.objects.get(id=post_id)
                        report = Report.objects.create(post=post, profile=profile, report_text=report_text)
                        report.save()
                        return redirect('profile')
                    except Exception:
                        return redirect('profile')

                elif type == 'entry':
                    try:
                        entry = Entry.objects.get(id=entry_id)
                        report = Report.objects.create(entry=entry, profile=profile, report_text=report_text)
                        report.save()
                        return redirect('profile')
                    except Exception:
                        return redirect('profile')

            else:
                return redirect('home')  # sadece burda
        except Exception:
            return render(request, 'error_view.html')


class EditPostApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                post_id = request.POST.get('post_id')
                entry_id = request.POST.get('entry_id')
                type = request.POST.get('type')
                if type == 'post':
                    post = Post.objects.get(id=post_id)

                    now = timezone.now()

                    categories = Category.objects.filter(type=0)
                    subcategories = Subcategory.objects.all()

                    return render(request, 'edit_post.html',
                                  {'profile': profile, 'type': type, 'post': post, 'now': now, 'categories': categories,
                                   'subcategories': subcategories})

            else:
                return redirect('home')  # sadece burda
        except Exception:
            return render(request, 'error_view.html')


class EditPostContentsApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                post_id = request.POST.get('post_id')
                post = Post.objects.get(id=post_id)
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                title = request.POST.get('post_title')
                description = request.POST.get('post_description')
                category_name = request.POST.get('post_categories')
                subcategory_name = request.POST.get('post_subcategories')
                price = request.POST.get('post_price')
                try:
                    file_input = request.FILES['file_input']
                except Exception:
                    pass
                category = Category.objects.get(name=category_name)
                subcategory = Subcategory.objects.get(name=subcategory_name)

                try:
                    try:
                        file_save = default_storage.save(file_input.name, file_input)
                        token = storage.child("postImages/" + file_input.name).put("media/" + file_input.name)
                        urll = storage.child("postImages/" + file_input.name).get_url(token)
                        delete = default_storage.delete(file_input.name)
                        post.post_image = file_input.name,
                        post.image_token = urll
                    except Exception:
                        pass

                    post.title = title
                    post.description = description
                    post.category = category
                    post.subcategory = subcategory
                    post.price = price
                    post.updated_at = timezone.now()

                    post.save()

                    categories = Category.objects.filter(type=0)
                    subcategories = Subcategory.objects.all()
                    posts = Post.objects.filter(id=post_id)
                    now = timezone.now()

                    return render(request, 'detailed_post.html',
                                  {'profile': profile, 'type': 'post', 'posts': posts, 'now': now, 'categories': categories,
                                   'subcategories': subcategories})
                except Exception:
                    message = 'Something went wrong, please try again!'
                    return render(request, 'add.html', {'message': message, 'profile': profile})

            else:
                return redirect('home')  # sadece burda
        except Exception:
            return render(request, 'error_view.html')


class ChatsApiView(APIView):
    def get(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:
                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                chats_owner = Chat.objects.filter(owner=profile).order_by('-created_at')
                chats_client = Chat.objects.filter(client=profile).order_by('-created_at')

                if len(chats_owner) == 0:
                    chats_owner = 'Empty'

                if len(chats_client) == 0:
                    chats_client = 'Empty'

                now = timezone.now()
                return render(request, 'chats.html',
                              {'profile': profile, 'chats_owner': chats_owner, 'chats_client': chats_client,
                               'now': now})  # sadece burda
            else:
                return redirect('home')
        except Exception:
            return render(request, 'error_view.html')


class ChatRoomApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                post_id = request.POST.get('post_id')
                if post_id is None or post_id == '':
                    post_id = request.POST.get('post_id_1')
                if post_id is None or post_id == '':
                    post_id = request.POST.get('post_id_2')
                post = Post.objects.get(id=post_id)

                if post.owner != profile:
                    try:
                        chat = Chat.objects.get(post=post, client=profile)
                    except Exception:
                        chat = Chat.objects.create(post=post,
                                                   owner=post.owner,
                                                   client=profile)
                        chat.save()
                else:
                    chat = Chat.objects.get(post=post, owner=profile)

                messages = Message.objects.filter(chat=chat)
                if len(messages) == 0:
                    messages = 'Empty'
                now = timezone.now()
                if messages != "Empty" and chat.get_last_message() is not None:
                    last_message_id = chat.get_last_message().id
                else:
                    last_message_id = 0
                return render(request, 'chat_room.html',
                              {'chat': chat, 'profile': profile, 'now': now, 'messages': messages, 'last_message_id': last_message_id})

            else:
                return redirect('home')  # sadece burda
        except Exception:
            return render(request, 'error_view.html')


class SendMessageApiView(APIView):
    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                message = request.POST.get('message').strip()
                chat_id = request.POST.get('chat_id')
                chat = Chat.objects.get(id=chat_id)
                now = timezone.now()

                try:
                    if chat.owner.id == profile.id:
                        message = Message.objects.create(chat=chat,
                                                         from_profile=profile,
                                                         to_profile=chat.client,
                                                         message=message)

                    else:
                        message = Message.objects.create(chat=chat,
                                                         from_profile=profile,
                                                         to_profile=chat.owner,
                                                         message=message)

                    message.save()

                except Exception:
                    message = 'Something went wrong, please try again!'
                    messages = Message.objects.filter(chat=chat)
                    if len(messages) == 0:
                        messages = 'Empty'
                    return render(request, 'chat_room.html',
                                  {'chat': chat, 'profile': profile, 'now': now, 'messages': messages, 'message': message})

                messages = Message.objects.filter(chat=chat)
                if len(messages) == 0:
                    messages = 'Empty'
                return render(request, 'chat_room.html',
                              {'chat': chat, 'profile': profile, 'now': now, 'messages': messages})

            else:
                return redirect('home')  # sadece burda
        except Exception:
            return render(request, 'error_view.html')


class SearchResultsApiView(View):
    def get(self, request):
        current_datetime = datetime.now()
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'), date_format)).total_seconds() / 60) > 60:
                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string
                user = User.objects.get(username=request.session['user_name'])
                profile = Profile.objects.get(user=user)
                current_time = datetime.now()

                search_term = request.GET.get('query')
                category = request.POST.get('post_categories')
                subcategory = request.POST.get('post_subcategories')
                posts = Post.objects.filter(status=1, is_sold=0).order_by('-created_at')

                if search_term:
                    # Filter posts by title or description containing the search term
                    posts = posts.filter(Q(title__icontains=search_term) |
                                         Q(description__icontains=search_term) |
                                         Q(owner__user__first_name__icontains=search_term) |
                                         Q(owner__user__last_name__icontains=search_term) |
                                         Q(owner__user__username__icontains=search_term))

                if category and category != '':
                    if subcategory and subcategory != '':
                        subcategory_obj = Subcategory.objects.get(name=subcategory)
                        posts = posts.filter(category__name=category, subcategory=subcategory_obj).order_by('-created_at')
                    else:
                        posts = posts.filter(category__name=category).order_by('-created_at')

                # Search for profiles based on first name, last name, and username
                profiles = Profile.objects.filter(Q(user__first_name__icontains=search_term) |
                                                  Q(user__last_name__icontains=search_term) |
                                                  Q(user__username__icontains=search_term))

                # Search for entries based on title or description containing the search term
                entries = Entry.objects.filter(Q(title__icontains=search_term) |
                                               Q(description__icontains=search_term) |
                                               Q(owner__user__first_name__icontains=search_term) |
                                               Q(owner__user__last_name__icontains=search_term) |
                                               Q(owner__user__username__icontains=search_term))

                if not posts.exists() and not profiles.exists() and not entries.exists():
                    entries = 'Empty'

                now = timezone.now()
                categories = Category.objects.filter(type=0)
                subcategories = Subcategory.objects.all()

                request.session['last_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")

                return render(request, 'search_results.html', {
                    'posts': posts,
                    'profiles': profiles,
                    'entries': entries,
                    'now': now,
                    'categories': categories,
                    'subcategories': subcategories})
        except Exception:
            return render(request, 'error_view.html')



class ChangePasswordApiView(APIView):
    def get(self, request):
        # This will handle the GET request and render the change_password page
        return render(request, 'change_password.html')

    def post(self, request):
        current_datetime = datetime.now()
        # Convert the datetime object to a string
        datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        date_format = "%Y-%m-%d %H:%M:%S"
        # Convert the string to a datetime object
        right_now = datetime.strptime(datetime_string, date_format)
        try:
            if 'last_time' in request.session and ((right_now - datetime.strptime(request.session.get('last_time'),
                                                                                  date_format)).total_seconds() / 60) > 60:

                request.session.flush()
                return redirect('home')
            elif 'logged_in' in request.session and request.session['logged_in']:
                current_datetime = datetime.now()
                # Convert the datetime object to a string
                datetime_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                request.session['last_time'] = datetime_string

            if request.method == 'POST':
                old_password = request.POST.get("old_password")
                new_password = request.POST.get("new_password1")
                confirm_password = request.POST.get("new_password2")

                #Check if the old password is valid
                user = authenticate(username=request.session['user_name'], password=old_password)

                if user is not None:
                    if new_password == confirm_password:
                        user.set_password(new_password)
                        user.save()
                        messages.success(request, 'Your password was successfully updated!')
                        return redirect('edit_profile')
                    else:
                        messages.error(request, 'New passwords are not matching')

                else:
                    messages.error(request, 'Incorrect old password')
            else:
                #form = ChangePasswordForm()
                return render(request, 'profile')
        except Exception:
            return render(request, 'error_view.html')


def get_categories(request, type):
    categories = Category.objects.filter(type=type).values('id', 'name')
    return JsonResponse(list(categories), safe=False)


def get_subcategories(request, category_id):
    subcategories = Subcategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)


last_refresh_timestamp = {}


def get_messages_by_chat_id(request, chat_id):
    messages = Message.objects.filter(chat=chat_id)
    data = {'messages': [{'id': msg.id, 'from_profile_id': msg.from_profile.id, 'from_profile_name': msg.from_profile.user.first_name, 'from_profile_last_name': msg.from_profile.user.last_name, 'profileimg': msg.from_profile.profile_image, 'text': msg.message} for msg in messages]}
    return JsonResponse(data)

@csrf_exempt
def trigger_refresh(request, chat_id):
    global last_refresh_timestamp
    last_refresh_timestamp[chat_id] = timezone.now()
    return JsonResponse({'status': 'ok'})

def get_last_refresh_timestamp(request, chat_id):
    global last_refresh_timestamp
    timestamp = last_refresh_timestamp.get(chat_id, timezone.now())
    return JsonResponse({'timestamp': timestamp.timestamp()})


@csrf_exempt
def favorite_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        user = User.objects.get(username=request.session['user_name'])
        profile = Profile.objects.get(user=user)
        try:
            action = Action.objects.get(post=post, profile=profile, type='favorite')

        except Exception:
            action = Action.objects.create(post=post, profile=profile, type='favorite')
            action.save()
            post.favorites_number += 1
            post.save()
    except Exception as e:
        pass


@csrf_exempt
def unfavorite_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        user = User.objects.get(username=request.session['user_name'])
        profile = Profile.objects.get(user=user)
        action = Action.objects.get(post=post, profile=profile, type='favorite')
        action.delete()
        post.favorites_number -= 1
        post.save()
    except Exception:
        pass


@csrf_exempt
def like_entry(request, entry_id):
    try:
        entry = Entry.objects.get(id=entry_id)
        user = User.objects.get(username=request.session['user_name'])
        profile = Profile.objects.get(user=user)
        try:
            action = Action.objects.get(entry=entry, profile=profile, type='like')

        except Exception:
            action = Action.objects.create(entry=entry, profile=profile, type='like')
            action.save()
            entry.likes_number += 1
            entry.save()

    except Exception as e:
        pass


@csrf_exempt
def unlike_entry(request, entry_id):
    try:
        entry = Entry.objects.get(id=entry_id)
        user = User.objects.get(username=request.session['user_name'])
        profile = Profile.objects.get(user=user)
        action = Action.objects.get(entry=entry, profile=profile, type='like')
        action.delete()
        entry.likes_number -= 1
        entry.save()
    except Exception:
        pass


client = openai.OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key="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",
)


def contains_inappropriate_content(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Replace with actual GPT-4 model name if available
            messages=[
                {"role": "system", "content": "You will act as a ethical guard for a university's social website. Determine if the following text contains any inappropriate content to be published, such as swear words or slang or drugs etc. in Turkish and English. Just return 'yes' or 'no'."},
                {"role": "user", "content": text}
            ]
        )

        # Extracting the result from the response
        result = response.choices[0].message.content.strip().lower()
        return "yes" in result

    except Exception as e:
        print(f"An error occurred: {e}")
        return False