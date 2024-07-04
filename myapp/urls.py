from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    
    path('home/', views.home, name='home'),
    path('integration/', views.integration, name='integration'),
    path('', views.login_view, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('instagram/', views.instagram_scrapper, name='instagram'),
    path('get_instagram_followers_details/', views.get_instagram_followers_details, name='get_instagram_followers_details'),
    path('get_instagram_followings_details/', views.get_instagram_followings_details, name='get_instagram_followings_details'),
    path('login_and_fetch_instagram_profile/', views.login_and_save_session, name='login_and_fetch_instagram_profile'),
    path('user_profile', views.user_details, name='user_profile'),
    path('proxy-instagram-image/', views.proxy_instagram_image, name='proxy_instagram_image'),
    path('fetch-followers-data/', views.fetch_followers_data, name='fetch_followers_data'),
    path('fetch-followings-data/', views.fetch_followings_data, name='fetch_followings_data'),




    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

]



