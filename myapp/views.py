from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from .forms import SignupForm, LoginForm
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required




from django.shortcuts import render, redirect
from .forms import SignupForm

def user_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'register.html', {'form': form})




from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponse

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
    return render(request, 'dashboard.html')

@login_required(login_url="/")
def integration(request):
    return render(request, 'integration.html')




# logout page
def user_logout(request):
    logout(request)
    return redirect('login')





