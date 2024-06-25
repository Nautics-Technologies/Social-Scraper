from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from .forms import SignupForm, LoginForm
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
import requests
from django.views.decorators.csrf import csrf_exempt
import instaloader
import json
import time
import logging
from .email import Osintgram # Ensure this imports the updated Osintgram class
from urllib3.exceptions import ProtocolError, SSLError
import re
from .models import ScrapedData
# Define regex patterns
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


import instaloader
import time
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from urllib3.exceptions import ProtocolError, SSLError
import requests

# Initialize Instaloader
L = instaloader.Instaloader()

# Constants
login_attempts = 1
scrape_duration = 50  # Duration for each scraping session in seconds
pause_duration = 3 * 60  # Pause duration between scraping sessions in seconds
max_failed_attempts = 2
logged_in_user = None



@csrf_exempt
def insta_login(request):
    global logged_in_user, L

    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')

            if not username or not password:
                return JsonResponse({'error': 'Username and password are required.'}, status=400)

            for attempt in range(login_attempts):
                set_proxy()
                try:
                    L.login(username, password)

                    request.session['username'] = username
                    request.session['password'] = password
                    logged_in_user = username
                    return redirect('instagram')
                except instaloader.exceptions.BadCredentialsException:
                    return redirect('home')
                except Exception as e:
                    time.sleep(10)  # Wait before retrying

            return JsonResponse({'error': 'Login failed: Could not log in after several attempts'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)


def user_details(request):
    global logged_in_user, L
    if request.method == 'GET':
        try:
            if not logged_in_user:
                return JsonResponse({'error': 'User not logged in.'}, status=400)
            
            profile = instaloader.Profile.from_username(L.context, logged_in_user)

            profile_info = {
                'username': profile.username,
                'User_id': profile.userid,
                'full_name': profile.full_name,
                'bio': profile.biography,
                'profile_pic': profile.profile_pic_url,
                'email': "None",
                'phone': "None",
                'followers': profile.followers,
                'followings': profile.followees,
                'total_posts': profile.mediacount,
                'external_url': profile.external_url,
            }

            return JsonResponse({'profile_data': profile_info}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def proxy_instagram_image(request):
    """
    Proxy view to fetch Instagram profile picture.
    """
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse(status=400)

    response = requests.get(image_url)
    if response.status_code == 200:
        content_type = response.headers['Content-Type']
        return HttpResponse(response.content, content_type=content_type)
    return HttpResponse(status=response.status_code)


from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ScrapedData
import instaloader
import random
import time
import json
import ssl
from urllib3.exceptions import ProtocolError, SSLError
import requests
import threading

ssl._create_default_https_context = ssl._create_unverified_context

# Initialize Instaloader
L = instaloader.Instaloader()

# Constants
login_attempts = 1
scrape_duration = 50  # Duration for each scraping session in seconds
pause_duration = 3 * 60  # Pause duration between scraping sessions in seconds
max_failed_attempts = 2  # Maximum number of failed scraping sessions before stopping


def fetch_proxies():
    proxy_api_url = 'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc'
    response = requests.get(proxy_api_url)
    proxy_list = response.json()['data']
    proxies = [f"{proxy['ip']}:{proxy['port']}" for proxy in proxy_list]
    return proxies

proxies = fetch_proxies()

# Function to set proxy
def set_proxy():
    proxy = random.choice(proxies)
    proxy_url = f"http://{proxy}"
    L.context._session.proxies = {'http': proxy_url, 'https': proxy_url}
    print(f"Using proxy: {proxy_url}")

# Function to login to Instagram
def instaloader_login(username, password):
    for attempt in range(login_attempts):
        set_proxy()  # Set a proxy before each login attempt
        try:
            L.login(username, password)
            print(f"Logged in (attempt {attempt + 1})")
            return True
        except Exception as e:
            print(f"Login failed on attempt {attempt + 1}: {e}")
            time.sleep(10)  # Wait before retrying
    return False


def save_data_to_db(data, profile_owner, data_type):
    for user in data:
        ScrapedData.objects.create(
            username=user['username'],
            user_id=user['User-id'],
            full_name=user['full_name'],
            profile_pic_url=user['profile_pic_url'],
            is_verified=user['is_verified'],
            is_private=user['is_private'],
            biography=user['biography'],
            external_url=user['external_url'],
            followers=user['followers'],
            followees=user['followees'],
            email=user['email'],
            phone_number=user['phone_number'],
            data_type=data_type,
            profile_owner=profile_owner
        )

def get_profile_data(profile, max_seconds, data_type, osintgram_instance, processed_usernames):
    data = []
    start_time = time.time()

    try:
        if data_type == "followers":
            iterator = profile.get_followers()
        elif data_type == "followings":
            iterator = profile.get_followees()
        else:
            return data
        
        for user in iterator:
            if time.time() - start_time > max_seconds:
                break
            
            if user.username in processed_usernames:
                continue  # Skip already processed usernames

            try:
                email, phone_number = osintgram_instance.get_user_contact_info(user.username)
            except Exception as e:
                print(f"Error fetching contact info for {user.username}: {e}")
                email, phone_number = '', ''

            # Extract email and phone number from biography if not found by Osintgram
            if not email:
                email_match = email_pattern.search(user.biography or "")
                email = email_match.group(0) if email_match else ''

            if not phone_number:
                phone_match = phone_pattern.search(user.biography or "")
                phone_number = phone_match.group(0) if phone_match else ''

            user_info = {
                "username": user.username,
                "User-id" : user.userid,
                "full_name": user.full_name,
                "profile_pic_url": user.profile_pic_url,
                "is_verified": user.is_verified,
                "is_private": user.is_private if hasattr(user, 'is_private') else None,  # Handle if attribute is not available
                "biography": user.biography,
                "external_url": user.external_url,
                "followers": user.followers,
                "followees": user.followees,
                "email": email,
                "phone_number": phone_number
            }
            data.append(user_info)
            processed_usernames.add(user.username)  # Add username to processed set

    except (instaloader.exceptions.ConnectionException, TimeoutError, ProtocolError, SSLError) as e:
        print(f"Connection exception occurred while scraping {data_type}: {e}")
    except instaloader.exceptions.QueryReturnedBadRequestException as e:
        print(f"Instagram API returned a bad request error: {e}")

    return data


@csrf_exempt
def scrape_data(request):
    if request.method == 'POST':
        username = request.session.get('username')
        password = request.session.get('password')

        if ScrapedData.objects.filter(profile_owner=username).exists():
            return JsonResponse({'status': 'exists', 'message': 'Data is already present in the database. You can see it or start scraping again.'})

        
        # profile_name = request.POST.get('profile_name')
        osintgram_instance = Osintgram(username, password)

        if not instaloader_login(username, password):
            return JsonResponse({"error": "Failed to log in after multiple attempts."}, status=500)

        # Get the target profile
        profile = instaloader.Profile.from_username(L.context, username)

        # Create a set of processed usernames to avoid duplicates
        processed_usernames = set()

        # Get initial followers and followings count
        total_followers_count = profile.followers
        total_following_count = profile.followees
        print(f"Total followers: {total_followers_count}")
        print(f"Total followings: {total_following_count}")

        failed_attempts = 0

        while True:
            if failed_attempts >= max_failed_attempts:
                print("Maximum failed attempts reached. Stopping scraping.")
                break

            print("Scraping followers...")
            set_proxy()  # Set a new proxy for each scraping session
            followers = get_profile_data(profile, scrape_duration, "followers", osintgram_instance, processed_usernames)
            if followers:
                save_data_to_db(followers, username, "followers")
                print(f"Collected {len(followers)} followers this session.")
            else:
                print("No new followers collected this session.")
                failed_attempts += 1

            print("Scraping followings...")
            set_proxy()  # Set a new proxy for each scraping session
            followings = get_profile_data(profile, scrape_duration, "followings", osintgram_instance, processed_usernames)
            if followings:
                save_data_to_db(followings, username, "followings")
                print(f"Collected {len(followings)} followings this session.")
            else:
                print("No new followings collected this session.")
                failed_attempts += 1

            if failed_attempts >= max_failed_attempts:
                print("Maximum failed attempts reached. Stopping scraping.")
                break

            # Pause between scraping sessions
            print(f"Pausing for {pause_duration / 60} minutes before next session.")
            time.sleep(pause_duration)

            # Re-login to ensure session validity
            if not instaloader_login(username, password):
                print("Re-login failed.")
                failed_attempts += 1
            else:
                failed_attempts = 0  # Reset failed attempts after a successful login

        print("Completed scraping.")
        L.close()

        return JsonResponse({"message": "Scraping completed successfully."})




from .models import ScrapedData

def fetch_followers_data(request):
    if request.method == 'GET':
        username = request.session.get('username')
        if not username:
            return JsonResponse({'error': 'User not logged in or session expired.'}, status=400)

        followers_data = ScrapedData.objects.filter(profile_owner=username, data_type='followers')
        followers_list = list(followers_data.values(
            'username', 'user_id', 'full_name', 'profile_pic_url', 'is_verified',
            'is_private', 'biography', 'external_url', 'followers', 'followees',
            'email', 'phone_number'
        ))

        return JsonResponse({'followers_data': followers_list}, status=200)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def fetch_followings_data(request):
    if request.method == 'GET':
        username = request.session.get('username')
        if not username:
            return JsonResponse({'error': 'User not logged in or session expired.'}, status=400)

        followings_data = ScrapedData.objects.filter(profile_owner=username, data_type='followings')
        followings_list = list(followings_data.values(
            'username', 'user_id', 'full_name', 'profile_pic_url', 'is_verified',
            'is_private', 'biography', 'external_url', 'followers', 'followees',
            'email', 'phone_number'
        ))

        return JsonResponse({'followings_data': followings_list}, status=200)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


    