from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    class Meta:
        db_table = "profile"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    auth_token = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_image = models.CharField(max_length=1000, default='https://firebasestorage.googleapis.com/v0/b/facid-6fd44.appspot.com/o/profilePhotos%2FUntitled_Artwork.png?alt=media&token')
    bio = models.CharField(max_length=200, default='Add a short bio here!')


class Category(models.Model):
    class Meta:
        db_table = "category"

    name = models.CharField(max_length=100)
    type = models.BooleanField(default=False)   # false for post, true for entry


class Subcategory(models.Model):
    class Meta:
        db_table = "subcategory"

    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='categories')


class Post(models.Model):
    class Meta:
        db_table = "post"

    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    post_image = models.CharField(max_length=500, null=True, blank=True)
    image_token = models.CharField(max_length=1000, null=True, blank=True)
    image_token1 = models.CharField(max_length=1000, null=True, blank=True)
    image_token2 = models.CharField(max_length=1000, null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    price = models.FloatField(null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    is_sold = models.BooleanField(default=False)
    favorites_number = models.IntegerField(default=0)

    POST_TYPES = (
        ('post_ad', 'PostAd'),
        ('borrow_ad', 'BorrowAd'),
        ('donate_ad', 'DonateAd')
    )
    type = models.CharField(max_length=20, choices=POST_TYPES, default='post_ad')

    def time_difference(self):
        now = timezone.now()
        time_difference = now - self.created_at
        return time_difference

    def favorite(self):
        self.favorites_number += 1

    def unfavorite(self):
        self.favorites_number -= 1


class DonateAd(Post):
    class Meta:
        db_table = "donate_ad"

    def save(self, *args, **kwargs):
        self.price = 0
        self.type = 'donate_ad'
        super().save(*args, **kwargs)


class BorrowAd(Post):
    class Meta:
        db_table = "borrow_ad"

    borrow_day = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        self.type = 'borrow_ad'
        super().save(*args, **kwargs)


class Entry(models.Model):
    class Meta:
        db_table = "entry"

    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    entry_image = models.CharField(max_length=500)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False)
    likes_number = models.IntegerField(default=0)

    def like(self):
        self.likes_number += 1

    def unlike(self):
        self.likes_number -= 1

    def time_difference(self):
        now = timezone.now()
        time_difference = now - self.created_at
        return time_difference


class Comment(models.Model):
    class Meta:
        db_table = "comment"

    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length=1000)
    status = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False)

    def time_difference(self):
        now = timezone.now()
        time_difference = now - self.created_at
        return time_difference


class Chat(models.Model):
    class Meta:
        db_table = "chat"

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    owner = models.ForeignKey(Profile, related_name='owner', on_delete=models.CASCADE)
    client = models.ForeignKey(Profile, related_name='client', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def time_difference(self):
        now = timezone.now()
        time_difference = now - self.created_at
        return time_difference

    def get_last_message(self):
        messages = Message.objects.filter(chat=self).order_by('-created_at')[0]
        if messages is None:
            return None
        else:
            return Message.objects.filter(chat=self).order_by('-created_at')[0]


class Message(models.Model):
    class Meta:
        db_table = "message"

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    from_profile = models.ForeignKey(Profile, related_name='profile_sent', on_delete=models.CASCADE)
    to_profile = models.ForeignKey(Profile, related_name='profile_received', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def time_difference(self):
        now = timezone.now()
        time_difference = now - self.created_at
        return time_difference


class Action(models.Model):
    class Meta:
        db_table = "action"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, null=True, blank=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    ACTION_TYPES = (
        ('like', 'Like'),
        ('favorite', 'Favorite'),
    )
    type = models.CharField(max_length=20, choices=ACTION_TYPES, default='favorite')


class Report(models.Model):
    class Meta:
        db_table = "report"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, null=True, blank=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    report_text = models.CharField(max_length=1000)
