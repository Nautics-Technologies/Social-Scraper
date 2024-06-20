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
login_attempts = 3
scrape_duration = 50  # Duration for each scraping session in seconds
pause_duration = 3 * 60  # Pause duration between scraping sessions in seconds
max_failed_attempts = 2
logged_in_user = None

@csrf_exempt
def insta_login(request):
    global logged_in_user, L

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'error': 'Username and password are required.'}, status=400)

            for attempt in range(login_attempts):
                try:
                    L.login(username, password)
                    request.session['username'] = username
                    request.session['password'] = password
                    logged_in_user = username
                    return JsonResponse({'message': 'Login successful'}, status=200)
                except instaloader.exceptions.BadCredentialsException:
                    return JsonResponse({'error': 'Login failed: Bad credentials'}, status=400)
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

def loggin(request):
    global L
    username = request.session.get('username')
    password = request.session.get('password')

    if not username or not password:
        print("Credentials not found in session.")
        return False

    for attempt in range(login_attempts):
        try:
            L.login(username, password)
            print(f"Logged in (attempt {attempt + 1})")
            return True
        except Exception as e:
            print(f"Login failed on attempt {attempt + 1}: {e}")
            time.sleep(10)  # Wait before retrying
            
        except instaloader.exceptions.CheckpointRequiredException as e:
            print(f"Login failed: Checkpoint required. Please visit the following URL to verify: {e.context.url}")
            break

    return False

def handle_rate_limit(error):
    if '429' in str(error):
        print("Rate limit exceeded. Sleeping for 5 minutes.")
        time.sleep(300)  # Sleep for 5 minutes
    else:
        raise error

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

            email, phone_number = osintgram_instance.get_user_contact_info(user.username)
            
            user_info = {
                "username": user.username,
                "User_id": user.userid,
                "full_name": user.full_name,
                # "profile_pic_url": user.profile_pic_url,
                "is_verified": user.is_verified,
                "is_private": user.is_private,
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
    except instaloader.exceptions.InstaloaderException as e:
        handle_rate_limit(e)
    
    return data

@csrf_exempt
def get_followers(request):
    if request.method == 'GET':
        try:
            if not loggin(request):
                return JsonResponse({'error': 'Login failed.'}, status=400)

            username = request.session.get('username')
            profile = instaloader.Profile.from_username(L.context, username)
            osintgram_instance = Osintgram(username, request.session.get('password'))
            osintgram_instance.login()

            # Retrieve processed usernames from session or initialize it
            processed_usernames = set(request.session.get('processed_usernames_followers', []))

            print("Scraping followers...")
            followers = get_profile_data(profile, scrape_duration, "followers", osintgram_instance, processed_usernames)
            print(f"Collected {len(followers)} followers.")

            # Update session with processed usernames
            request.session['processed_usernames_followers'] = list(processed_usernames)

            return JsonResponse({'followers': followers}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)

@csrf_exempt
def get_followings(request):
    if request.method == 'GET':
        try:
            if not loggin(request):
                return JsonResponse({'error': 'Login failed.'}, status=400)

            username = request.session.get('username')
            profile = instaloader.Profile.from_username(L.context, username)
            osintgram_instance = Osintgram(username, request.session.get('password'))
            osintgram_instance.login()

            # Retrieve processed usernames from session or initialize it
            processed_usernames = set(request.session.get('processed_usernames_followings', []))

            print("Scraping followings...")
            followings = get_profile_data(profile, scrape_duration, "followings", osintgram_instance, processed_usernames)
            print(f"Collected {len(followings)} followings.")

            # Update session with processed usernames
            request.session['processed_usernames_followings'] = list(processed_usernames)

            return JsonResponse({'followings': followings}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)







