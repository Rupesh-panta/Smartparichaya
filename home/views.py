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
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from .utils import *
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse as DjangoJsonResponse, HttpResponse
import logging
import secrets
import os
from django.http import JsonResponse
import PyPDF2

from .models import Vacancy
from .utils import match_job_template
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
import urllib.parse

from django.urls import reverse
import urllib.parse

@login_required
def apply_job(request, job_id):
    # 1. Fetch the specific job details
    job = get_object_or_404(Vacancy, id=job_id)
    
    # 2. Prepare the data to be sent to the CV Editor
    params = {
        'target_job': job.title,
        'required_skills': job.skills,
        'company': job.company_name,
        'auto_optimize': 'true'
    }
    query_string = urllib.parse.urlencode(params)
    
    # 3. Inform the user
    messages.info(request, f"Redirecting to CV Builder. Let's tailor your CV for the {job.title} role!")
    
    # 4. FIX: Ensure return is indented correctly and URL name matches urls.py
    # If your urls.py has: path('cv-editor/', views.cv_editor, name='cv_editor')
    url = reverse('cv_editor') 
    return redirect(f"{url}?{query_string}")

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
import urllib.parse

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Vacancy, id=job_id)
    
    # Data to pass to the editor
    params = {
        'target_job': job.title,
        'required_skills': job.skills,
        'company': job.company_name,
    }
    query_string = urllib.parse.urlencode(params)
    
    # reverse('cv_editor') will return '/testUserAuth/cv-editor/'
    url = reverse('cv_editor') 
    
    return redirect(f"{url}?{query_string}")

# Change 'def jobs_view(request):' to 'def jobs(request):'
@login_required(login_url='/login/')
def jobs(request):
    raw_vacancies = Vacancy.objects.all()
    
    processed_vacancies = []
    for job in raw_vacancies:
        # 1. Handle skills list (split string into list for the UI)
        skills_list = []
        if job.skills:
            skills_list = [s.strip() for s in job.skills.split(',')]
        
        # 2. Run your template matching algorithm from utils.py
        template_choice = match_job_template(job.title, skills_list)
        
        # 3. MAPPING DATA (Fixes the AttributeError)
        processed_vacancies.append({
            'title': job.title,
            'company': job.company_name,
            # We use job.skills here because job.description DOES NOT EXIST
            'description': job.skills, 
            'skills_list': skills_list,
            'matched_template': template_choice,
        })

    return render(request, 'jobs.html', {'vacancies': processed_vacancies})

@login_required
def cv_editor(request):
    # Retrieve the job data from the URL parameters
    target_job = request.GET.get('target_job')
    required_skills = request.GET.get('required_skills')
    
    context = {
        'target_job': target_job,
        'required_skills': required_skills,
        'is_job_specific': True if target_job else False,
        # ... your existing context (e.g., username, profile data) ...
    }
    return render(request, 'cv-editor.html', context)

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
            content = page.extract_text()
            if content:
                text += content
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None
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
        'title': 'Smart Parichaya | Your CV Buddy',
        'active_page': 'home',
        'blogs': blogs,
        'feedbacks': feedbacks,
    }
    return render(request, 'home.html', data)


def about(request):
    # return HttpResponse("About me")
    data = {
        'title': 'About - Smart Parichaya',
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
        'title': 'Blog - Smart Parichaya',
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
        'title': 'FAQs - Smart Parichaya',
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
        'title': 'Contact - Smart Parichaya',
        'active_page': 'contact',
    }
    return render(request, 'contact.html', data)


def loginSmartParichaya(request):
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
            'title': 'Sign in - Smart Parichaya',

        }
        return render(request, 'smartparichaya.html', data)


def logoutSmartParichaya(request):
    logout(request)
    return redirect('/login/')


def signupSmartparichaya(request):

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
            subject = 'Welcome to Smart Parichaya!'
            message = (
                f"Hi {username},\n\n"
                "Thank you for registering at Smart Parichaya. We are excited to help you craft your best resumes and test your CV score!\n\n"
                "Feel free to explore our platform, and reach out if you have any questions.\n\n"
                "Best regards,\n"
                "The Smart Parichaya Team"
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
            'title': 'Signup - Smart Parichaya',
        }
        return render(request, 'smartparichayasignup.html', data)


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
        'title': 'Dashboard | Smart Parichaya',
        'section': section
    }
    return render(request, 'testuserAuth.html', context)


from django.urls import reverse

@login_required(login_url='/login/')
def dashboard(request, section=None):
    username = request.user.username
    email = request.user.email
    
    # 1. Ensure you are getting the profile OBJECT, not a function
    # Note: Use models.Profile if your model is in the same file or imported as models
    profile, created = models.Profile.objects.get_or_create(user=request.user)

    social_account = SocialAccount.objects.filter(user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get('picture') if social_account else None
    
    # 2. Logic for profile picture
    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        profile_picture_url = google_profile_picture
    else:
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    # 3. Handle Template Counts (Library Size vs User History)
    # Total available designs
    template_library_count = 4 
    
    # User's specific history
    res_count_obj = models.ResumeCount.objects.filter(user=request.user).first()
    attempts_count = res_count_obj.count if res_count_obj else 0

    # 4. Feedback logic
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        models.Feedback.objects.create(user=request.user, rating=rating, comment=comment)
        return redirect('testUserAuth')

    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Smart Parichaya | Dashboard',
        'section': section,
        'template_count': template_library_count, # Shows 4
        'resume_attempts': attempts_count,        # Shows user history (e.g. 11)
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='/login/')
def CvBuilder(request, section=None):
    username = request.user.username
    email = request.user.email
    social_account = SocialAccount.objects.filter(user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get('picture') if social_account else None
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    profile, created = models.Profile.objects.get_or_create(user=request.user)

    if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png':
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        profile_picture_url = google_profile_picture
    else:
        profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'

    # MANUALLY ADD TEMPLATE DATA HERE
    templates_data = [
        {"name": "Advanced - Forest", "id": "advanced-0", "preview": "advanced-0.png"},
        {"name": "Minimal - Snow", "id": "minimalist-1", "preview": "minimalist-1.png"},
        {"name": "Advanced - Modern", "id": "advanced-2", "preview": "advanced-2.png"},
        {"name": "Professional - 1", "id": "professional-1", "preview": "professional-1.png"},
    ]

    from django.urls import reverse # Ensure this is imported at the top

    # ... previous code (templates_data, etc.) ...

    if request.method == "POST":
        # Handle Template Selection
        template_id = request.POST.get('template_id')
        
        # This MUST be indented inside the POST block
        if template_id:
            request.session['selected_template'] = template_id
            
            resume_count, created = models.ResumeCount.objects.get_or_create(user=request.user)
            resume_count.count += 1
            resume_count.save()
            
            return redirect(reverse('cv_editor'))

        # Handle Feedback submission (also inside the POST block)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating:
            models.Feedback.objects.create(user=request.user, rating=rating, comment=comment)
            return redirect('testUserAuth')

    # This runs for GET requests

    resume_count, created = models.ResumeCount.objects.get_or_create(user=request.user)

    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Smart Parichaya | CV-Builder',
        'section': section,
        'template_count': resume_count.count if resume_count else 0,
        'templates': templates_data, # NEW: Pass templates to HTML
    }
    return render(request, 'cv-builder.html', context)
def jobs(request):
    # This is where you decide which template to recommend
    # For testing, let's just pick "Alien"
    context = {
        'recommendation': 'Alien', 
    }
    return render(request, 'future_templates.html', context)

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
        'title': 'Smart Parichaya | Cover-Letter',
        'section': section
    }
    return render(request, 'coverletter.html', context)


from django.contrib import messages

from django.shortcuts import render, redirect
# Use an ALIAS (DjangoJsonResponse) to prevent UnboundLocalError
from django.http import JsonResponse as DjangoJsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from . import models

@login_required(login_url='/login/')
def resumeScore(request):
    # --- 1. SET DEFAULTS AT THE VERY TOP ---
    # This ensures 'score' and 'recommendation' exist for both GET and POST
    score = 0 
    recommendation = "Serenity"

    # --- 2. Verification Gate ---
    try:
        if not request.user.profile.is_verified:
            return redirect('dashboard')
    except Exception:
        return redirect('dashboard')

    # --- 3. Handle POST (The AJAX upload) ---
    if request.method == "POST":
        if request.FILES.get('resume'):
            resume_file = request.FILES['resume']
            text = extract_text_from_pdf(resume_file)
            
            if text:
                keywords = ['python', 'django', 'javascript', 'react', 'sql', 'html', 'css', 'api', 'git']
                matches = [w for w in keywords if w in text.lower()]
                score = min(100, (len(matches) * 10) + 15)
            
            return DjangoJsonResponse({
                'score': score,
                'resultClass': 'success' if score >= 50 else 'warning'
            })

    # --- 4. Logic for GET Request (Normal Page Load) ---
    # Now this code can run safely even if POST was skipped
    if score > 80:
        recommendation = "Alien"
    elif score > 50:
        recommendation = "Column Mint"

    context = {
        'username': request.user.username,
        'recommendation': recommendation,
        'score': score,
    }
    
    # Make sure you are rendering the right template name here
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
        'title': 'Smart Parichaya | Resume-Score',
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
        'title': 'Smart Parichaya | Resume-Score',
        'section': section,
        'prediction_result': prediction_result,
        'prediction_class': prediction_class,
    }

    return render(request, 'resume-score.html', context)

@login_required(login_url='/login/')
def jobs(request, section=None):
    # 1. Boilerplate for User Profile/UI
    username = request.user.username
    email = request.user.email
    social_account = SocialAccount.objects.filter(user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get('picture') if social_account else None
    profile, created = models.Profile.objects.get_or_create(user=request.user)
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    profile_picture_url = (
        profile.profile_picture.url
        if profile.profile_picture and profile.profile_picture.url != '/media/profile_pics/user-circle_svgrepo.com.png'
        else google_profile_picture or '/media/profile_pics/user-circle_svgrepo.com.png'
    )

    # 2. FETCH VACANCIES & RUN ALGORITHM
    raw_vacancies = models.Vacancy.objects.all().order_by('-posted_at')
    processed_vacancies = []
    
    for job in raw_vacancies:
        # Split skills string into a list
        skills_list = [s.strip() for s in job.skills.split(',')]
        
        # Apply your Rule-Based Algorithm from utils.py
        template_choice = match_job_template(job.title, skills_list)
        
        processed_vacancies.append({
            'id': job.id,
            'title': job.title,
            # We map the database field 'skills' to the dictionary key 'description'
            'description': job.skills, 
            'skills_list': skills_list,
            'matched_template': template_choice,
        })

    # 3. Context for the template
    context = {
        'username': username,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'title': 'Smart Parichaya | Jobs',
        'section': section,
        'vacancies': processed_vacancies # THIS IS CRUCIAL
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
        'title': 'Smart Parichaya | Feedback',
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
        'title': 'Smart Parichaya | Profile',
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


import os
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# 1. This handles JUST the profile picture removal
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
import os

# Fix for AttributeError: 'delete_profile_picture'
@login_required
def delete_profile_picture(request):
    profile = request.user.profile
    if profile.profile_picture:
        # Check if the file exists on your MacBook and delete it
        if os.path.exists(profile.profile_picture.path):
            os.remove(profile.profile_picture.path)
        
        profile.profile_picture = None
        profile.save()
        return JsonResponse({'status': 'success', 'message': 'Picture deleted'})
    return JsonResponse({'status': 'error', 'message': 'No picture found'})

# Fix for AttributeError: 'update_username'
@login_required
def update_username(request):
    if request.method == 'POST':
        new_username = request.POST.get('username')
        if new_username:
            request.user.username = new_username
            request.user.save()
            messages.success(request, "Username updated successfully!")
        return redirect('profile') # Adjust this to your profile URL name
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

from django.contrib.auth import logout # Add this import

from django.contrib.auth import logout # Crucial import

@login_required
def delete_profile(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    
    try:
        user = request.user
        # Log out BEFORE deleting the user record
        logout(request) 
        user.delete() 
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
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
        subject='Your Smart Parichaya password was changed',
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
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # Ensure these functions return strings/serialized data for session storage
        public_key, private_key = generate_rsa_keys()
        encrypted_otp = rsa_encrypt(otp, public_key)

        request.session['encrypted_otp'] = encrypted_otp
        request.session['private_key'] = private_key

        try:
            # FIX: Joined the message strings properly
            message = (
                f"The verification code to verify your Smart Parichaya account is {otp}.\n\n"
                "Kindly provide this code in the application to complete your request. "
                "Do not share this with anyone.\n\n"
                "Best regards,\nSmart Parichaya Team"
            )
            
            send_mail(
                subject='Your OTP for Verification',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'OTP sent, check your email', 'email': user_email})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

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
    # FIX: Check the profile model, not the User model
    is_verified = request.user.profile.is_verified 
    return JsonResponse({'is_verified': is_verified})

# reset forgotten password

def generate_otp():
    otp = ''.join([str(secrets.choice(range(10))) for _ in range(6)])
    return otp


def forgot_password(request):
    context = {
        'title': 'Smart Parichaya | Forgot-Password',
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
            subject = 'Password Reset OTP for Smart Parichaya'
            message = (
    f"Dear {user.username},\n\n"
    f"The verification code to reset your Smart Parichaya password is {otp}.\n\n"
    "Kindly provide this code in the application to complete your password reset request, "
    "and do not share this with anyone.\n\n"
    "Best regards,\n"
    "Smart Parichaya Team"
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
                subject='Your Smart Parichaya password was changed',
                message='Your password has been successfully changed. If you did not make this change, please contact support.',
                from_email='noreply@simpfolio.com',
                recipient_list=[email],
                fail_silently=False,
            )

            return JsonResponse({'status': 'success'}, status=200)

        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


from .models import Vacancy # Ensure this is imported

@login_required(login_url='/login/')
def cv_editor(request, section=None):
    # 1. Retrieve the Selected Template from Session
    selected_template = request.session.get('selected_template', 'advanced-0')

    # 2. Standard User/Profile Logic
    username = request.user.username
    email = request.user.email
    social_account = SocialAccount.objects.filter(user=request.user, provider='google').first()
    google_profile_picture = social_account.extra_data.get('picture') if social_account else None
    
    profile, created = models.Profile.objects.get_or_create(user=request.user)
    feedback_count = models.Feedback.objects.filter(user=request.user).count()

    profile_picture_url = '/media/profile_pics/user-circle_svgrepo.com.png'
    if profile.profile_picture and profile.profile_picture.url != profile_picture_url:
        profile_picture_url = profile.profile_picture.url
    elif google_profile_picture:
        profile_picture_url = google_profile_picture

    # 3. VACANCY LOGIC
    all_vacancies = Vacancy.objects.all()
    vacancy_count = all_vacancies.count()
    best_match_score = 98 if vacancy_count > 0 else 0

    # 4. JOB TAILORING LOGIC (Catch data from 'Apply Now')
    target_job = request.GET.get('target_job')
    raw_skills = request.GET.get('required_skills', '')
    
    # We clean the skills here so the template doesn't have to use 'replace'
    # This splits by comma or space and removes extra characters
    skills_list = [s.strip().replace(',', '') for s in raw_skills.split(',') if s.strip()]
    if not skills_list and raw_skills: # Fallback if split by comma failed
        skills_list = [s.strip().replace(',', '') for s in raw_skills.split() if s.strip()]

    context = {
        'username': username,
        'first_name': request.user.first_name,
        'email': email,
        'profile_picture': profile_picture_url,
        'google_profile_picture': google_profile_picture,
        'feedback_count': feedback_count,
        'selected_template': selected_template,
        
        'vacancies': all_vacancies,
        'vacancy_count': vacancy_count,
        'best_match': best_match_score,
        
        # New Job Specific Context
        'target_job': target_job,
        'required_skills_list': skills_list,
        'is_job_specific': True if target_job else False,
        
        'title': f'Smart Parichaya | Editing {selected_template}',
        'section': section
    }

    return render(request, 'CVEditor.html', context)