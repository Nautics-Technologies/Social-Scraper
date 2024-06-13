from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from .forms import SignupForm, LoginForm
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
import instaloader
import json



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
    return render(request, 'Dashboard.html')


@login_required(login_url="/")
def integration(request):
    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        print(user_name)
        profile_info_json = get_instagram_profile_info(user_name)
        print(profile_info_json)
        return render(request, 'integration.html', {'profile': profile_info_json})
    return render(request, 'integration.html')

def forgot_password(request):
    return render(request, 'forgot-password.html')


# logout page
def user_logout(request):
    logout(request)
    return redirect('login')


def get_instagram_profile_info(username):
    L = instaloader.Instaloader()

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        profile_info = {
            "username": profile.username,
            "user_id": profile.userid,
            "name": profile.full_name,
            "total_posts": profile.mediacount,
            "followers": profile.followers,
            "followees": profile.followees,
            "biography": profile.biography,
            "is_private": profile.is_private,
            "is_verified": profile.is_verified,
            "is_business_account": profile.is_business_account
        }
        return profile_info
    except Exception as e:
        return {"error": str(e)}


