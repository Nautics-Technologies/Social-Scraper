from django.db import models

# Create your models here.


class ScrapedData(models.Model):
    username = models.CharField(max_length=150)
    user_id = models.CharField(max_length=50)
    full_name = models.CharField(max_length=150)
    profile_pic_url = models.URLField()
    is_verified = models.BooleanField(default=False)
    is_private = models.BooleanField(null=True)
    biography = models.TextField(null=True, blank=True)
    external_url = models.URLField(null=True, blank=True)
    followers = models.IntegerField(null=True)
    followees = models.IntegerField(null=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    data_type = models.CharField(max_length=20)  # 'followers' or 'followings'
    profile_owner = models.CharField(max_length=150)  # Username of the profile being scraped

    class Meta:
        unique_together = ('username', 'data_type', 'profile_owner')


class InstagramProfile(models.Model):
    username = models.CharField(max_length=150, unique=True)
    user_id = models.BigIntegerField()
    full_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    profile_pic = models.URLField(blank=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    followers = models.IntegerField()
    followings = models.IntegerField()
    total_posts = models.IntegerField()
    external_url = models.URLField(blank=True, null=True)  # Updated field


    def __str__(self):
        return self.username