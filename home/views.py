from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from home import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from allauth.socialaccount.models import SocialAccount
import json
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .utils import *
from django.views.decorators.csrf import csrf_exempt
import logging
import secrets
import os
import PyPDF2




# Ensure NLTK resources are only downloaded once
nltk_data_path = os.path.join(os.path.expanduser("~"), "nltk_data")  # Set a directory for nltk data
stopwords_path = os.path.join(nltk_data_path, "corpora", "stopwords")
wordnet_path = os.path.join(nltk_data_path, "corpora", "wordnet")


# Create your views here.



# Utility to extract text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        text = "Error extracting text. Please try another file."
    return text


def home(request):
    blogs = models.Blog.objects.filter(feature_on_home=True)
    feedbacks = models.Feedback.objects.filter(feature_on_home=True)

    for feedback in feedbacks:
        # Get or create user profile
        profile, created = models.Profile.objects.get_or_create(
            user=feedback.user)

        # Check for Google account to retrieve profile picture
        social_account = SocialAccount.objects.filter(
            user=feedback.user, provider='google').first()
        google_profile_picture = social_account.extra_data.get(
            'picture') if social_account else None

        # Determine profile picture URL
        if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
            # Custom profile picture exists
            feedback.profile_picture_url = profile.profile_picture.url
        elif google_profile_picture:
            # Google profile picture exists
            feedback.profile_picture_url = google_profile_picture
        else:
            # Default profile picture
            feedback.profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    data = {
        'title': 'Simpfolio | Your CV Buddy',
        'active_page': 'home',
        'blogs': blogs,
        'feedbacks': feedbacks,
    }
    return render(request, 'home.html', data)


def about(request):
    # return HttpResponse("About me")
    data = {
        'title': 'About - Simpfolio',
        'active_page': 'about',
    }
    return render(request, 'about.html', data)


def blog(request):
    highlighted_blog = models.Blog.objects.filter(
        feature_on_blog_highlights=True).first()
    latest_blogs = models.Blog.objects.filter(
        feature_on_blog_latest_posts=True)
    popular_blogs = models.Blog.objects.filter(
        feature_on_blog_popular_posts=True)

    data = {
        'title': 'Blog - Simpfolio',
        'active_page': 'blog',
        'latest_blogs': latest_blogs,
        'popular_blogs': popular_blogs,
        'highlighted_blog': highlighted_blog


    }

    return render(request, 'blog.html', data)


# This slug comes from urls.py ("blog/<slug>") and that <slug> icomes from our blog.html where i have used <a href="/blog/{{blogs.1.slug}}"> and that is the slug of the second object(blog) in the model Blog.
def blogpost(request, slug):
    # For dynamic blog contents to be acessible in the blogPost.html where this (slug=slug) compares and matches the slug coming from the databse with the one from the urls.py
    blogs = models.Blog.objects.filter(slug=slug).first()
    data = {
        'title': blogs.blogTitle,
        'active_page': 'blog',
        'blogs': blogs,
    }
    return render(request, "blogpost.html", data)


def faq(request):
    # return HttpResponse("faq")
    data = {
        'title': 'FAQs - Simpfolio',
        'active_page': 'faq',
    }
    return render(request, 'faq.html', data)


def contact(request):
    if request.method == 'POST':

        # the (name="") field is used in request.POST[''] method here , eg name="email" is used as request.POST['email] here as parameter and it is a dictionary.

        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']

        try:

            contact = models.Contact(
                name=name, email=email, subject=subject, message=message)
            contact.save()
            print("Data written to the Database successfully")
            return JsonResponse({'success': True})

        except Exception as e:
            print(f"Error saving form data to the Database:{str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})

    else:
        print("Get Request invoked")

    data = {
        'title': 'Contact - Simpfolio',
        'active_page': 'contact',
    }
    return render(request, 'contact.html', data)


def loginSimpfolio(request):
    if request.user.is_authenticated:
        return redirect('/testUserAuth/')

    if request.method == 'POST':
        loginEmail = request.POST['email']
        loginPassword = request.POST['password']

        user = authenticate(request, username=loginEmail,
                            password=loginPassword)
        if user is not None:
            login(request, user)
            return JsonResponse({
                'status': 'success'
            },
                status=200)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid email or password'
            },
                status=400)

    else:
        data = {
            'title': 'Sign in - Simpfolio',

        }
        return render(request, 'SimpfolioLogin.html', data)


def logoutSimpfolio(request):
    logout(request)
    return redirect('/login/')


def signupSimpfolio(request):

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'status': 'fail', 'message': 'An account with this email address already exists.'}, status=400)

        # Create new user
        try:
            myUser = User.objects.create_user(username, email, password)
            myUser.save()

            # Send welcome email
            subject = 'Welcome to Simpfolio!'
            message = (
                f"Hi {username},\n\n"
                "Thank you for registering at Simpfolio. We are excited to help you craft your best resumes and test your CV score!\n\n"
                "Feel free to explore our platform, and reach out if you have any questions.\n\n"
                "Best regards,\n"
                "The Simpfolio Team"
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]

            send_mail(subject, message, from_email,
                      recipient_list, fail_silently=False)

            return JsonResponse({'status': 'success', 'message': 'Your account has been created.'}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Something went wrong!'}, status=500)
    else:
        data = {
            'title': 'Signup - Simpfolio',
        }
        return render(request, 'SimpfolioSignup.html', data)


@login_required(login_url='/login/')
def testUserAuth(request, section=None):
    # Get the username and email from the authenticated user
    username = request.user.username
    email = request.user.email

    social_account = SocialAccount.objects.filter(
        user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get(
        'picture') if social_account else None

    profile, created = models.Profile.objects.get_or_create(user=request.user)

    # Count the feedbacks submitted by the logged-in user
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    # Determine profile picture URL
    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        # Custom profile picture exists
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        # Google profile picture exists
        profile_picture_url = google_profile_picture
    else:
        # Default profile picture
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    # Debug logs
    print("Profile Picture URL:", profile_picture_url)
    print("Google Profile Picture URL:", google_profile_picture)

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        user = request.user
        models.Feedback.objects.create(
            user=user, rating=rating, comment=comment)
        return redirect('testUserAuth')

    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Dashboard | Simpfolio',
        'section': section
    }
    return render(request, 'testuserAuth.html', context)


@login_required(login_url='/login/')
def dashboard(request, section=None):
    # Get the username and email from the authenticated user
    username = request.user.username
    email = request.user.email
    social_account = SocialAccount.objects.filter(
        user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get(
        'picture') if social_account else None
    # Count the feedbacks submitted by the logged-in user
    feedback_count = models.Feedback.objects.filter(user=request.user).count()
    # Get or create user profile
    profile, created = models.Profile.objects.get_or_create(user=request.user)

    # Determine profile picture URL
    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        # Custom profile picture exists
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        # Google profile picture exists
        profile_picture_url = google_profile_picture
    else:
        # Default profile picture
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    # Debug logs
    print("Profile Picture URL:", profile_picture_url)
    print("Google Profile Picture URL:", google_profile_picture)

    # Retrieve template count from the database (ResumeCount model)
    resume_count = models.ResumeCount.objects.filter(user=request.user).first()
    template_count = resume_count.count if resume_count else 0

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        user = request.user
        models.Feedback.objects.create(
            user=user, rating=rating, comment=comment)
        return redirect('testUserAuth')

    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Simpfolio | Dashboard',
        'section': section,
        'template_count': template_count,
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='/login/')
def CvBuilder(request, section=None):
    # Get the username and email from the authenticated user
    username = request.user.username
    email = request.user.email
    social_account = SocialAccount.objects.filter(
        user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get(
        'picture') if social_account else None
    # Count the feedbacks submitted by the logged-in user
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    # Get or create user profile
    profile, created = models.Profile.objects.get_or_create(user=request.user)

    # Determine profile picture URL
    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        # Custom profile picture exists
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        # Google profile picture exists
        profile_picture_url = google_profile_picture
    else:
        # Default profile picture
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    # Debug logs
    print("Profile Picture URL:", profile_picture_url)
    print("Google Profile Picture URL:", google_profile_picture)

    # Handle the "Select Template" button click
    if request.method == "POST":

        resume_count, created = models.ResumeCount.objects.get_or_create(
            user=request.user)

        resume_count.count += 1
        resume_count.save()
        return redirect('/cv-editor/')

    # Always load the page with resume count information
    resume_count, created = models.ResumeCount.objects.get_or_create(
        user=request.user)

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        user = request.user
        models.Feedback.objects.create(
            user=user, rating=rating, comment=comment)
        return redirect('testUserAuth')

    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Simpfolio | CV-Builder',
        'section': section,
        'template_count': resume_count.count if resume_count else 0,
    }
    return render(request, 'cv-builder.html', context)


@login_required(login_url='/login/')
def coverLetter(request, section=None):
    # Get the username and email from the authenticated user
    username = request.user.username
    email = request.user.email
    social_account = SocialAccount.objects.filter(
        user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get(
        'picture') if social_account else None

    # Count the feedbacks submitted by the logged-in user
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    # Get or create user profile
    profile, created = models.Profile.objects.get_or_create(user=request.user)

    # Determine profile picture URL
    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        # Custom profile picture exists
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        # Google profile picture exists
        profile_picture_url = google_profile_picture
    else:
        # Default profile picture
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    # Debug logs
    print("Profile Picture URL:", profile_picture_url)
    print("Google Profile Picture URL:", google_profile_picture)

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        user = request.user
        models.Feedback.objects.create(
            user=user, rating=rating, comment=comment)
        return redirect('testUserAuth')

    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Simpfolio | Cover-Letter',
        'section': section
    }
    return render(request, 'coverletter.html', context)


@login_required(login_url='/login/')
def resumeScore(request, section=None):
    # Get user details
    username = request.user.username
    email = request.user.email
    social_account = SocialAccount.objects.filter(
        user=request.user, provider='google'
    ).first()
    google_profile_picture = social_account.extra_data.get(
        'picture') if social_account else None

    # Count feedbacks
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    # Get or create profile
    profile, created = models.Profile.objects.get_or_create(user=request.user)
    profile_picture_url = (
        profile.profile_picture.url
        if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png'
        else google_profile_picture or '/media/profile_pics/user-circle_svgrepo.com.png'
    )

from django.shortcuts import render
from django.http import JsonResponse
import logging

def resume_upload_view(request):
    # Initialize variables
    prediction_result = None
    prediction_class = None
    prediction_score = 0  # Default score as percentage
    result_class = "error"  # Default result class
    cleaned_text = ""
    probabilities = None
    max_probability = None

    if request.method == "POST" and request.FILES.get('resume'):
        resume_file = request.FILES['resume']  # Get uploaded file
        try:
            # Extract text from PDF
            text = extract_text_from_pdf(resume_file)

            if text:
                cleaned_text = text.strip()
                prediction_class = "N/A"
                prediction_score = 0
                prediction_result = "Resume uploaded successfully. Text extracted for viewing."
                result_class = "success"
            else:
                cleaned_text = ""
                prediction_class = "No text found in PDF"
                prediction_score = 0
                prediction_result = "Could not extract any text from the resume."
                result_class = "error"

            # Debugging prints
            print(f"Extracted Text: {text[:500]}\n\n")  # First 500 chars
            print(f"Cleaned Text: {cleaned_text}")
            print(f"Probabilities: {probabilities}")
            print(f"Max Probability: {max_probability}")
            print(f"Prediction Class: {prediction_class}")
            print(f"Score: {prediction_score}")

        except Exception as e:
            logging.error(f"Error processing resume: {e}")
            cleaned_text = "Error reading the file."
            prediction_class = "Error"
            prediction_score = 0
            prediction_result = "An error occurred while processing the resume."
            result_class = "error"

        # Handle AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'score': prediction_score,
                'result': prediction_result,
                'resultClass': result_class,
            })

    # Render template for normal requests
    context = {
        'prediction_result': prediction_result,
        'prediction_class': prediction_class,
        'prediction_score': prediction_score,
        'cleaned_text': cleaned_text,
    }
    return render(request, 'resume-score.html', context)


    from django.http import JsonResponse
from django.shortcuts import render

def resume_upload_view(request):    
    # Initialize variables
    prediction_result = ""
    prediction_class = ""
    prediction_score = 0
    result_class = "error"
    username = request.user.username if request.user.is_authenticated else ""
    email = request.user.email if request.user.is_authenticated else ""
    profile_picture_url = ""
    google_profile_picture = ""
    feedback_count = 0
    section = "resume"

    # Handle POST file upload
    if request.method == "POST" and request.FILES.get('resume'):
        resume_file = request.FILES['resume']
        try:
            # Extract text from the uploaded resume (PDF)
            text = extract_text_from_pdf(resume_file)

            if text:
                cleaned_text = text.strip()
                prediction_score = 0
                prediction_result = "Resume uploaded successfully. Text extracted for viewing."
                result_class = "success"
            else:
                cleaned_text = ""
                prediction_score = 0
                prediction_result = "Could not extract any text from the resume."
                result_class = "error"

        except Exception as e:
            import logging
            logging.error(f"Error processing resume: {e}")
            cleaned_text = "Error reading the file."
            prediction_score = 0
            prediction_result = "An error occurred while processing the resume."
            result_class = "error"

        # Handle AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'score': prediction_score,
                'result': prediction_result,
                'resultClass': result_class,
            })

    # Render HTML template for normal requests
    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Simpfolio | Resume-Score',
        'section': section,
        'prediction_result': prediction_result,
        'prediction_class': prediction_class,
    }
    return render(request, 'resume-score.html', context)


    # Context for the HTML template
    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Simpfolio | Resume-Score',
        'section': section,
        'prediction_result': prediction_result,
        'prediction_class': prediction_class,
    }

    return render(request, 'resume-score.html', context)

@login_required(login_url='/login/')
def jobs(request, section=None):
    # Get the username and email from the authenticated user
    username = request.user.username
    email = request.user.email

    social_account = SocialAccount.objects.filter(
        user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get(
        'picture') if social_account else None

    profile, created = models.Profile.objects.get_or_create(user=request.user)

    # Count the feedbacks submitted by the logged-in user
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    # Determine profile picture URL
    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        # Custom profile picture exists
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        # Google profile picture exists
        profile_picture_url = google_profile_picture
    else:
        # Default profile picture
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    # Debug logs
    print("Profile Picture URL:", profile_picture_url)
    print("Google Profile Picture URL:", google_profile_picture)

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        user = request.user
        models.Feedback.objects.create(
            user=user, rating=rating, comment=comment)
        return redirect('testUserAuth')

    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Simpfolio | Jobs',
        'section': section
    }
    return render(request, 'jobs.html', context)


@login_required(login_url='/login/')
def feedback(request, section=None):
    # Get the username and email from the authenticated user
    username = request.user.username
    email = request.user.email
    social_account = SocialAccount.objects.filter(
        user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get(
        'picture') if social_account else None

    profile, created = models.Profile.objects.get_or_create(user=request.user)

    # Count the feedbacks submitted by the logged-in user
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        # Custom profile picture exists
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        # Google profile picture exists
        profile_picture_url = google_profile_picture
    else:
        # Default profile picture
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    # Debug logs
    print("Profile Picture URL:", profile_picture_url)
    print("Google Profile Picture URL:", google_profile_picture)

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        user = request.user
        models.Feedback.objects.create(
            user=user, rating=rating, comment=comment)
        return redirect('testUserAuth')

    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Simpfolio | Feedback',
        'section': section
    }
    return render(request, 'feedback.html', context)


@login_required(login_url='/login/')
def profile(request, section=None):
    username = request.user.username
    email = request.user.email
    user = request.user
    is_google_authenticated = SocialAccount.objects.filter(
        user=user, provider='google').exists()
    password_set = user.has_usable_password()

    # Fetch Google account
    social_account = SocialAccount.objects.filter(
        user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get(
        'picture') if social_account else None

    # Count feedback
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    # Get or create user profile
    profile, created = models.Profile.objects.get_or_create(user=request.user)

    # Determine profile picture URL
    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        # Custom profile picture exists
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        # Google profile picture exists
        profile_picture_url = google_profile_picture
    else:
        # Default profile picture
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    # Debug logs
    print("Profile Picture URL:", profile_picture_url)
    print("Google Profile Picture URL:", google_profile_picture)

    context = {
        'username': username,
        'user': user,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Simpfolio | Profile',
        'section': section,
        'is_google_authenticated': is_google_authenticated,
        'password_set': password_set,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='/login/')
def upload_profile_picture(request):
    if request.method == 'POST':
        profile, created = models.Profile.objects.get_or_create(
            user=request.user)

        # Handle the profile picture upload
        if 'profile_picture' in request.FILES:
            # Check if there's an existing profile picture and delete it
            if profile.profile_picture and profile.profile_picture.name != 'profile_pics/user-circle_svgrepo.com.png':
                # Delete the old profile picture
                profile.profile_picture.delete(save=False)

            # Set the new profile picture
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            return JsonResponse({'status': 'success'}, status=200)
        else:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)


@login_required(login_url='/login/')
def delete_profile_picture(request):
    if request.method == 'DELETE':
        profile, created = models.Profile.objects.get_or_create(
            user=request.user)

        # Only allow deletion if the user has uploaded a profile picture
        if profile.profile_picture and profile.profile_picture.name != 'profile_pics/user-circle_svgrepo.com.png':
            profile.profile_picture.delete(save=False)
            # Reset to default picture
            profile.profile_picture = 'profile_pics/user-circle_svgrepo.com.png'
            profile.save()
            return JsonResponse({'status': 'success'}, status=200)
        else:
            return JsonResponse({'status': 'error', 'message': 'No picture to delete or default picture.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)


def update_username(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_username = data.get('username')

        if new_username and request.user.is_authenticated:
            # Check if username already exists
            if User.objects.filter(username=new_username).exists():
                return JsonResponse({'status': 'error', 'message': 'Username already taken!'}, status=400)

            # Update the authenticated user's username
            request.user.username = new_username
            request.user.save()

            return JsonResponse({'status': 'success', 'message': 'Username updated successfully!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid request!'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid method!'}, status=405)


@login_required
def change_password(request):
    if request.method == 'POST':
        user = request.user
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('retype_password', '')

        # Check if the new password and confirm password match
        if new_password != confirm_password:
            return JsonResponse({'status': 'error', 'message': 'New password and confirmation do not match'})

        # Validate password strength using Django's validators
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': ', '.join(e.messages)})

        # Check if the user is a Google authenticated user
        if SocialAccount.objects.filter(user=user, provider='google').exists():
            # Check if the user already has a password set
            if user.has_usable_password():
                # For Google-authenticated users who have set a password, check the current password
                if not user.check_password(current_password):
                    return JsonResponse({'status': 'error', 'message': 'Current password is incorrect'})
            # Google users setting the password for the first time don't need current password check
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep the user logged in

            send_password_change_email(user.email)
            return JsonResponse({'status': 'success', 'message': 'Password set successfully'})

        # For normal users, check the current password
        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep the user logged in

            send_password_change_email(user.email)
            return JsonResponse({'status': 'success', 'message': 'Password changed successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Current password is incorrect'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def send_password_change_email(email):
    send_mail(
        subject='Your Simpfolio password was changed',
        message='Your password has been successfully changed. If you did not make this change, please contact support.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


# account verification part

@login_required
def send_verification_otp(request):
    if request.method == 'POST':
        user_email = request.user.email

        # Step 1: Generate a 6-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # Step 2: Generate RSA keys
        public_key, private_key = generate_rsa_keys()

        # Step 3: Encrypt the OTP using the public key
        encrypted_otp = rsa_encrypt(otp, public_key)

        # Step 4: Store encrypted OTP and private key securely in the session
        request.session['encrypted_otp'] = encrypted_otp
        request.session['private_key'] = private_key

        # Step 5: Send the OTP via email to the user
        try:
            send_mail(
                subject='Your OTP for Verification',
               message = f'The verification code to reset your Simpfolio password is {otp}.'

                f'Kindly provide this code in the application to complete your account verification request, '
                'and do not share this with anyone.\n\n'
                'Best regards,\n'
                'Simpfolio Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'OTP sent, check your email', 'email': user_email})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Failed to send OTP email.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def verify_otp(request):
    if request.method == 'POST':
        input_data = json.loads(request.body)
        input_otp = input_data.get('otp')

        # Retrieve the encrypted OTP and private key from session
        encrypted_otp = request.session.get('encrypted_otp')
        private_key = request.session.get('private_key')

        if encrypted_otp and private_key:
            # Decrypt the OTP
            decrypted_otp = rsa_decrypt(encrypted_otp, private_key)

            # Compare the decrypted OTP with the user input
            if str(input_otp).strip() == str(decrypted_otp).strip():
                # If matched, mark the user as verified
                request.user.profile.is_verified = True
                request.user.profile.save()
                return JsonResponse({'status': 'verified'})
            else:
                return JsonResponse({'status': 'invalid OTP'})

        return JsonResponse({'status': 'error', 'message': 'Unable to verify OTP'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def check_verification_status(request):
    is_verified = request.user.is_verified
    return JsonResponse({'is_verified': is_verified})


# reset forgotten password

def generate_otp():
    otp = ''.join([str(secrets.choice(range(10))) for _ in range(6)])
    return otp


def forgot_password(request):
    context = {
        'title': 'Simpfolio | Forgot-Password',
    }

    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = generate_otp()

            # Save OTP in the session or use a different method to store the OTP
            request.session['otp'] = otp
            request.session['email'] = email

            # Prepare email content
            subject = 'Password Reset OTP for Simpfolio'
            message = (
    f"Dear {user.username},\n\n"
    f"The verification code to reset your Simpfolio password is {otp}.\n\n"
    "Kindly provide this code in the application to complete your password reset request, "
    "and do not share this with anyone.\n\n"
    "Best regards,\n"
    "Simpfolio Team"
)

            # Send email with OTP
            send_mail(
                subject,
                message,
                'simpfolio4u@gmail.com',
                [email],
                fail_silently=False,
            )
            return JsonResponse({"status": "otp_sent"}, status=200)
        except User.DoesNotExist:
            # Return JSON here
            return JsonResponse({"status": "email_not_found"}, status=404)

    return render(request, 'forgot-password.html', context)


def verify_otp_for_password(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')

        if entered_otp == session_otp:
            return JsonResponse({"status": "otp_verified"}, status=200)
        else:
            return JsonResponse({"status": "otp_invalid"}, status=400)


def reset_password(request):
    if request.method == "POST":
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        email = request.session.get('email')

        if new_password == confirm_password:
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                return JsonResponse({"status": "password_reset_successful"}, status=200)
            except User.DoesNotExist:
                return JsonResponse({"status": "user_not_found"}, status=404)
        else:
            return JsonResponse({"status": "password_mismatch"}, status=400)
    return JsonResponse({"status": "invalid_request"}, status=400)


@csrf_exempt
def update_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')

        try:
            user = User.objects.get(email=email)

            # Check if the new password is the same as the current password
            if user.check_password(new_password):
                return JsonResponse({'status': 'same_as_current'}, status=400)

            # Update the password if it's different
            user.set_password(new_password)
            user.save()
            send_mail(
                subject='Your Simpfolio password was changed',
                message='Your password has been successfully changed. If you did not make this change, please contact support.',
                from_email='noreply@simpfolio.com',
                recipient_list=[email],
                fail_silently=False,
            )

            return JsonResponse({'status': 'success'}, status=200)

        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@login_required(login_url='/login/')
def cv_editor(request, section=None):
    username = request.user.username
    email = request.user.email
    social_account = SocialAccount.objects.filter(
        user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get(
        'picture') if social_account else None
    # Count the feedbacks submitted by the logged-in user
    feedback_count = models.Feedback.objects.filter(user=request.user).count()
    # Get or create user profile
    profile, created = models.Profile.objects.get_or_create(user=request.user)

    # Determine profile picture URL
    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        # Custom profile picture exists
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        # Google profile picture exists
        profile_picture_url = google_profile_picture
    else:
        # Default profile picture
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

        # Debug logs
    print("Profile Picture URL:", profile_picture_url)
    print("Google Profile Picture URL:", google_profile_picture)

    context = {
        'username': username,
        'first_name': request.user.first_name,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Simpfolio | Dashboard',
        'section': section
    }

    return render(request, 'CVEditor.html', context)
