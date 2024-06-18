from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from .forms import SignupForm, LoginForm
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
import instaloader
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import instaloader
import json
import time
import logging


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








# import json
# import requests
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# import instaloader
# import logging

# logger = logging.getLogger(__name__)

# logged_in_user = None


# @csrf_exempt
# def insta_login(request):
#     global logged_in_user
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             username = data.get('username')
#             password = data.get('password')

#             if not username or not password:
#                 return JsonResponse({'error': 'Username and password are required.'}, status=400)

#             session = requests.Session()
#             session.get('https://www.instagram.com/accounts/login/')
#             csrf_token = session.cookies['csrftoken']  # Extract CSRF token from cookies

#             login_payload = {
#                 'username': username,
#                 'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:&:{password}',  # Instagram may require this format
#             }

#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#                 'X-CSRFToken': csrf_token,
#                 'X-Instagram-AJAX': '1',  # Version number of the AJAX request
#                 'X-Requested-With': 'XMLHttpRequest',
#             }

#             login_url = 'https://www.instagram.com/accounts/login/ajax/'
#             response = session.post(login_url, data=login_payload, headers=headers)

#             if response.status_code == 200 and response.json().get('authenticated'):
#                 logged_in_user = username
#                 return JsonResponse({'message': 'Login successful', 'user': response.json()}, status=200)
#             else:
#                 return JsonResponse({'error': 'Login failed', 'details': response.json()}, status=400)

#         except Exception as e:
#             logger.error(f'Error during login: {str(e)}')
#             return JsonResponse({'error': str(e)}, status=400)

#     return JsonResponse({'error': 'Invalid HTTP method'}, status=405)



import json
import instaloader
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

# Global variables to store the login status and session
L = instaloader.Instaloader()
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

            try:
                L.login(username, password)
                logged_in_user = username
                return JsonResponse({'message': 'Login successful'}, status=200)
            except instaloader.exceptions.BadCredentialsException:
                return JsonResponse({'error': 'Login failed: Bad credentials'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Login failed: {str(e)}'}, status=400)

        except Exception as e:
            logger.error(f'Error during login: {str(e)}')
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)


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


def user_details(request):
    global logged_in_user, L
    if request.method == 'GET':
        try:
            if not logged_in_user:
                return JsonResponse({'error': 'User not logged in.'}, status=400)
            
            profile = instaloader.Profile.from_username(L.context, logged_in_user)

            profile_info = {
                'username': profile.username,
                'full_name': profile.full_name,
                'bio': profile.biography,
                'profile_pic': profile.profile_pic_url,  # Make sure this key matches
                'email': "None",  # Placeholder if email is not available
                'phone': "None",  # Placeholder if phone is not available
                'followers': profile.followers,  # Make sure this key matches
                'followings': profile.followees,  # Make sure this key matches
                'total_posts': profile.mediacount,  # Make sure this key matches
                'external_url': profile.external_url,
            }

            return JsonResponse({'profile_data': profile_info}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)



@csrf_exempt
def get_followers(request):
    global logged_in_user, L
    if request.method == 'GET':
        try:
            if not logged_in_user:
                return JsonResponse({'error': 'User not logged in.'}, status=400)

            profile = instaloader.Profile.from_username(L.context, logged_in_user)
            followers = [{'username': follower.username, 
                        'full_name': follower.full_name, 
                        'email': "-",  # Placeholder if email is not available
                        'phone': "-",
                        'External URL': follower.external_url,
                        'bio':follower.biography,
                        'Address':"-",
                        } 
                        for follower in profile.get_followees()]

            return JsonResponse({'followers': followers}, status=200)

        except Exception as e:
            logger.error(f'Error retrieving followers: {str(e)}')
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)

@csrf_exempt
def get_following(request):
    global logged_in_user, L
    if request.method == 'GET':
        try:
            if not logged_in_user:
                return JsonResponse({'error': 'User not logged in.'}, status=400)

            profile = instaloader.Profile.from_username(L.context, logged_in_user)
            following = [{'username': followee.username, 
                          'full_name': followee.full_name, 
                          'profile_pic_url': followee.profile_pic_url  ,                  
                          'email': "-",  # Placeholder if email is not available
                          'phone': "-",
                          'External URL': followee.external_url,
                          'bio':followee.biography,
                          'Address':"-",
                          
                        } for followee in profile.get_followers()]

            return JsonResponse({'following': following}, status=200)

        except Exception as e:
            logger.error(f'Error retrieving following: {str(e)}')
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)
