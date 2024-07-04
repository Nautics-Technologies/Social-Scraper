from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from .forms import SignupForm, LoginForm
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
import requests
from django.views.decorators.csrf import csrf_exempt

import json
import time
import logging
from .email import Osintgram # Ensure this imports the updated Osintgram class
from urllib3.exceptions import ProtocolError, SSLError
import re
import requests



email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
phone_pattern = re.compile(r'\b(?:\+?(\d{1,3})?[-.\s]?)?(\d{1,4})[-.\s]?(\d{1,4})[-.\s]?(\d{1,9})\b')



def user_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'register.html', {'form': form})




def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not username or not password:
            return render(request, 'login.html', {
                'error_message': "Username and password are required."
            })

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Replace 'home' with your success redirect URL
        else:
            return render(request, 'login.html', {
                'error_message': "Invalid login credentials"
            })
    return render(request, 'login.html')




@login_required(login_url="/")
def home(request):
    return render(request, 'workspace-preference.html')


@login_required(login_url="/")
def integration(request):
    return render(request, 'integration.html')


def forgot_password(request):
    return render(request, 'forgot-password.html')

def instagram_scrapper(request):
    return render(request, 'instagram.html')


# logout page
def user_logout(request):
    logout(request)
    return redirect('login')



import os
import random
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, BadPassword
import logging
from .models import InstagramProfile,Follower,Following

logger = logging.getLogger()

# Ensure the sessions directory exists
SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)


@csrf_exempt
def login_and_save_session(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')

            if not username or not password:
                return JsonResponse({'error': 'Username and password are required.'}, status=400)
            
            try:
                cl = Client()
                cl.login(username, password)
                session_file = os.path.join(SESSIONS_DIR, f"{username}_session.json")
                cl.dump_settings(session_file)
                get_and_save_instagram_profile(username)
                request.session['username'] = username
                return JsonResponse({'message': 'Login successful'}, status=200)
            
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)  


logger = logging.getLogger(__name__)

def get_and_save_instagram_profile(username):
    try:
        session_file = os.path.join(SESSIONS_DIR, f"{username}_session.json")
        cl = Client()
        
        try:
            cl.load_settings(session_file)
            cl.login(username, '')
            cl.account_info()  # Ensure session is valid
        except Exception as e:
            logger.error(f"Failed to login or validate session for {username}: {e}")
            return JsonResponse({'error': 'Failed to login or validate session'}, status=400)

        try:
            profile = cl.user_info_by_username(username)
            time.sleep(random.uniform(1, 3))  # Add random delay to mimic human behavior

            # Check if the profile already exists
            existing_profile = InstagramProfile.objects.filter(user_id=profile.pk).first()
            if existing_profile:
                # Update existing profile data
                existing_profile.username = profile.username
                existing_profile.full_name = profile.full_name
                existing_profile.bio = profile.biography
                existing_profile.profile_pic = profile.profile_pic_url
                existing_profile.email = profile.public_email or "None"
                existing_profile.phone = profile.public_phone_number or "None"
                existing_profile.followers_count = profile.follower_count
                existing_profile.followings_count = profile.following_count
                existing_profile.total_posts = profile.media_count
                existing_profile.external_url = profile.external_url or ""

                existing_profile.save()
                return JsonResponse({'message': 'Profile data updated successfully'}, status=200)
            else:
                # Save profile data to the database if it doesn't exist
                InstagramProfile.objects.create(
                    username=profile.username,
                    user_id=profile.pk,
                    full_name=profile.full_name,
                    bio=profile.biography,
                    profile_pic=profile.profile_pic_url,
                    email=profile.public_email or "None",
                    phone=profile.public_phone_number or "None",
                    followers_count=profile.follower_count,
                    followings_count=profile.following_count,
                    total_posts=profile.media_count,
                    external_url=profile.external_url or "",
                )

                return JsonResponse({'message': 'Profile data saved successfully'}, status=200)
        except Exception as e:
            logger.error(f"Error saving profile data for {username}: {e}")
            return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error in get_and_save_instagram_profile for {username}: {e}")
        return JsonResponse({'error': str(e)}, status=400)




@csrf_exempt
def user_details(request):
    if request.method == 'GET':
        # Assuming the username is stored in the session
        username = request.session.get('username')

        if not username:
            return JsonResponse({'error': 'User not logged in.'}, status=400)

        try:
            profile = InstagramProfile.objects.get(username=username)

            profile_info = {
                'username': profile.username,
                'user_id': profile.user_id,
                'full_name': profile.full_name,
                'bio': profile.bio,
                'profile_pic': profile.profile_pic,
                'email': profile.email,
                'phone': profile.phone,
                'followers': profile.followers_count,
                'followings': profile.followings_count,
                'total_posts': profile.total_posts,
                'external_url': profile.external_url,
            }

            return JsonResponse({'profile_data': profile_info}, status=200)
        except InstagramProfile.DoesNotExist:
            return JsonResponse({'error': 'Profile not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)



def proxy_instagram_image(request):

    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse(status=400)

    response = requests.get(image_url)
    if response.status_code == 200:
        content_type = response.headers['Content-Type']
        return HttpResponse(response.content, content_type=content_type)
    return HttpResponse(status=response.status_code)

# Set up logging


import os
import time
import random
import logging
import re
from django.http import JsonResponse
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, RateLimitError, ClientError

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define regex patterns for email and phone extraction from bio
email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
phone_pattern = re.compile(r'\+?\d[\d -]{8,}\d')


@csrf_exempt
def get_instagram_followers_details(request):
    if request.method == 'POST':
        try:
            username = request.session.get('username')
            if not username:
                return JsonResponse({'error': 'No user is logged in'}, status=400)

            session_file = os.path.join(SESSIONS_DIR, f"{username}_session.json")
            cl = Client()
            cl.load_settings(session_file)

            try:
                logger.info(f"Loading session file for user: {username}")
                cl.login(username, '')  # Password is not needed here because we are using the session
                cl.account_info()  # Check if the session is valid
                logger.info(f"Logging in using session for user: {username}")
            except LoginRequired:
                logger.error(f"Session is invalid for user: {username}. Please log in again.")
                return JsonResponse({'error': 'Session is invalid. Please log in again.'}, status=400)

            user_id = cl.user_id_from_username(username)
            logger.info(f"Fetching user ID for user: {username}")
            followers = []
            processed_user_ids = set()
            amount_to_fetch = 100

            while len(followers) < amount_to_fetch:
                try:
                    results = cl.user_followers(user_id, amount=amount_to_fetch - len(followers))
                    new_followers = [f for f in results.values() if f.pk not in processed_user_ids]
                    followers.extend(new_followers)
                    processed_user_ids.update(f.pk for f in new_followers)
                    logger.info(f"Fetched {len(followers)} followers so far for user: {username}")
                    time.sleep(random.uniform(2, 5))  # Add random delay to mimic human behavior

                    if len(results) < (amount_to_fetch - len(followers)):
                        break

                except RateLimitError:
                    logger.warning(f"Rate limit reached. Retrying after a delay for user: {username}")
                    time.sleep(60)
                except ClientError as e:
                    logger.error(f"Client error occurred: {e}")
                    break

            profile = InstagramProfile.objects.get(username=username)
            logger.info(f"Saving followers data to database for user: {username}")

            for follower in followers:
                user_info = cl.user_info(follower.pk)
                email = user_info.public_email or "None"
                phone = user_info.public_phone_number or "None"

                # Check bio for email and phone if not found traditionally
                if email == "None":
                    email_match = email_pattern.search(user_info.biography)
                    if email_match:
                        email = email_match.group(0)
                if phone == "None":
                    phone_match = phone_pattern.search(user_info.biography)
                    if phone_match:
                        phone = phone_match.group(0)

                # Save follower details to the database
                Follower.objects.create(
                    instagram_profile=profile,
                    username=user_info.username,
                    user_id=user_info.pk,
                    full_name=user_info.full_name,
                    bio=user_info.biography,
                    profile_pic=user_info.profile_pic_url,
                    email=email,
                    phone=phone,
                    follower_count=user_info.follower_count,
                    following_count=user_info.following_count,
                    media_count=user_info.media_count,
                    external_url=user_info.external_url if user_info.external_url else "",  # Handle missing field
                    is_private=user_info.is_private,
                    is_verified=user_info.is_verified,
                )

            return JsonResponse({'message': 'Followers data scraped successfully'}, status=200)

        except Exception as e:
            logger.error(f"Error in get_instagram_followers_details: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)


csrf_exempt

def get_instagram_followings_details(request):
    if request.method == 'POST':
        try:
            username = request.session.get('username')
            if not username:
                return JsonResponse({'error': 'No user is logged in'}, status=400)

            session_file = os.path.join(SESSIONS_DIR, f"{username}_session.json")
            cl = Client()
            cl.load_settings(session_file)

            try:
                logger.info(f"Loading session file for user: {username}")
                cl.login(username, '')  # Password is not needed here because we are using the session
                cl.account_info()  # Check if the session is valid
                logger.info(f"Logging in using session for user: {username}")
            except LoginRequired:
                logger.error(f"Session is invalid for user: {username}. Please log in again.")
                return JsonResponse({'error': 'Session is invalid. Please log in again.'}, status=400)

            user_id = cl.user_id_from_username(username)
            logger.info(f"Fetching user ID for user: {username}")
            followings = []
            processed_user_ids = set()
            amount_to_fetch = 100

            while len(followings) < amount_to_fetch:
                try:
                    results = cl.user_following(user_id, amount=amount_to_fetch - len(followings))
                    new_followers = [f for f in results.values() if f.pk not in processed_user_ids]
                    followings.extend(new_followers)
                    processed_user_ids.update(f.pk for f in new_followers)
                    logger.info(f"Fetched {len(followings)} followings so far for user: {username}")
                    time.sleep(random.uniform(2, 5))  # Add random delay to mimic human behavior

                    if len(results) < (amount_to_fetch - len(followings)):
                        break

                except RateLimitError:
                    logger.warning(f"Rate limit reached. Retrying after a delay for user: {username}")
                    time.sleep(60)
                except ClientError as e:
                    logger.error(f"Client error occurred: {e}")
                    break

            profile = InstagramProfile.objects.get(username=username)
            logger.info(f"Saving followings data to database for user: {username}")

            for following in followings:
                user_info = cl.user_info(following.pk)
                email = user_info.public_email or "None"
                phone = user_info.public_phone_number or "None"

                # Check bio for email and phone if not found traditionally
                if email == "None":
                    email_match = email_pattern.search(user_info.biography)
                    if email_match:
                        email = email_match.group(0)
                if phone == "None":
                    phone_match = phone_pattern.search(user_info.biography)
                    if phone_match:
                        phone = phone_match.group(0)

                # Save following details to the database
                Following.objects.create(
                    instagram_profile=profile,
                    username=user_info.username,
                    user_id=user_info.pk,
                    full_name=user_info.full_name,
                    bio=user_info.biography,
                    profile_pic=user_info.profile_pic_url,
                    email=email,
                    phone=phone,
                    follower_count=user_info.follower_count,
                    following_count=user_info.following_count,
                    media_count=user_info.media_count,
                    external_url=user_info.external_url if user_info.external_url else "",  # Handle missing field
                    is_private=user_info.is_private,
                    is_verified=user_info.is_verified,
                )

            return JsonResponse({'message': 'Followings data scraped successfully'}, status=200)

        except Exception as e:
            logger.error(f"Error in get_instagram_followings_details: {e}")
            return JsonResponse({'error': str(e)}, status=400)





@csrf_exempt
def fetch_followers_data(request):
    if request.method == 'GET':
        username = request.session.get('username')
        if not username:
            return JsonResponse({'error': 'User not logged in or session expired.'}, status=400)

        try:
            profile = InstagramProfile.objects.get(username=username)
            followers_data = profile.follower_set.all()
            followers_list = list(followers_data.values(
                'username', 'user_id', 'full_name', 'profile_pic', 'is_verified',
                'is_private', 'bio', 'external_url', 'follower_count', 'following_count',
                'email', 'phone'
            ))

            return JsonResponse({'followers_data': followers_list}, status=200)

        except InstagramProfile.DoesNotExist:
            return JsonResponse({'error': 'User profile does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def fetch_followings_data(request):
    if request.method == 'GET':
        username = request.session.get('username')
        if not username:
            return JsonResponse({'error': 'User not logged in or session expired.'}, status=400)

        try:
            profile = InstagramProfile.objects.get(username=username)
            followings_data = profile.following_set.all()
            followings_list = list(followings_data.values(
                'username', 'user_id', 'full_name', 'profile_pic', 'is_verified',
                'is_private', 'bio', 'external_url', 'follower_count', 'following_count',
                'email', 'phone'
            ))

            return JsonResponse({'followings_data': followings_list}, status=200)

        except InstagramProfile.DoesNotExist:
            return JsonResponse({'error': 'User profile does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)
