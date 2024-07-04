from django.db import models

class InstagramProfile(models.Model):
    username = models.CharField(max_length=150, unique=True)
    user_id = models.BigIntegerField(unique=True)
    full_name = models.CharField(max_length=150)
    bio = models.TextField(null=True, blank=True)
    profile_pic = models.URLField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    followers_count = models.IntegerField()
    followings_count = models.IntegerField()
    total_posts = models.IntegerField()
    external_url = models.URLField(max_length=200, null=True, blank=True)


class Follower(models.Model):
    instagram_profile = models.ForeignKey(InstagramProfile, on_delete=models.CASCADE, related_name='follower_set')
    username = models.CharField(max_length=150)
    user_id = models.BigIntegerField()
    full_name = models.CharField(max_length=150)
    bio = models.TextField(null=True, blank=True)
    profile_pic = models.URLField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    follower_count = models.IntegerField()
    following_count = models.IntegerField()
    media_count = models.IntegerField()
    external_url = models.URLField(max_length=200, null=True, blank=True)
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)


class Following(models.Model):
    instagram_profile = models.ForeignKey(InstagramProfile, on_delete=models.CASCADE, related_name='following_set')
    username = models.CharField(max_length=150)
    user_id = models.BigIntegerField()
    full_name = models.CharField(max_length=150)
    bio = models.TextField(null=True, blank=True)
    profile_pic = models.URLField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    follower_count = models.IntegerField()
    following_count = models.IntegerField()
    media_count = models.IntegerField()
    external_url = models.URLField(max_length=200, null=True, blank=True)
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
