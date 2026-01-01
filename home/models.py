from django.db import models
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from django.utils.dateformat import DateFormat
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, Group, Permission

# Create your models here.


class Contact(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    subject = models.TextField()
    message = models.TextField()

    def __str__(self):
        return self.name + "-" + self.email


class Blog(models.Model):
    blogNo = models.AutoField(primary_key=True)
    blogTitle = models.CharField(max_length=200)
    blogCategory = models.CharField(max_length=100)
    blogPreviewBody = models.TextField()
    blogContentIntro = models.TextField()
    blogTopic1 = models.CharField(max_length=200)
    blogTopic1Content = models.TextField()
    blogTopic2 = models.CharField(max_length=200)
    blogTopic2Content = models.TextField()
    blogTopic3 = models.CharField(max_length=200)
    blogTopic3Content = models.TextField()
    blogTopic4 = models.CharField(max_length=200)
    blogTopic4Content = models.TextField()
    blogConclusionHeading = models.CharField(max_length=200)
    blogConclusionContent = models.TextField()
    slug = models.CharField(max_length=100)
    blogAuthor = models.CharField(max_length=50)
    postTime = models.DateField(auto_now_add=True)
    blogImage = models.ImageField(upload_to="blog-section/blogThumbnails", default="")

    feature_on_home = models.BooleanField(default=False)
    feature_on_blog_highlights = models.BooleanField(default=False)
    feature_on_blog_latest_posts = models.BooleanField(default=False)
    feature_on_blog_popular_posts = models.BooleanField(default=False)

    def formattedPostTime(self):
        return self.postTime.strftime("%B %d, %Y")

    def __str__(self):
        return (
            self.blogTitle
            + " - "
            + self.blogAuthor
            + " : "
            + str(self.formattedPostTime())
        )


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    feature_on_home = models.BooleanField(default=False)

    def get_profile_picture(self):
        try:
            social_account = SocialAccount.objects.get(
                user=self.user, provider="google"
            )
            # Assuming 'picture' holds the URL for Google profile pictures
            return social_account.extra_data.get("picture", None)
        except SocialAccount.DoesNotExist:
            return None

    def formatted_date(self):
        return DateFormat(self.created_at).format("M d, Y")

    def __str__(self):
        return f"{self.user.username} - {self.rating} stars"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", default="profile_pics/user-circle_svgrepo.com.png"
    )
    is_verified = models.BooleanField(default=False)


class ResumeCount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def formatted_date(self):
        return DateFormat(self.last_updated).format("M d, Y")

    def __str__(self):
        return f"{self.user.username} - {self.count} resumes created"

# home/models.py
from django.db import models

# ... keep your existing models (Contact, Blog, Profile, etc.) ...

class Vacancy(models.Model):  # Ensure 'V' is capital and it inherits from models.Model
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    skills = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title