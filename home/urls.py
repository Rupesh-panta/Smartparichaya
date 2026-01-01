from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from home import views # All views are called via this import

admin.site.site_header = "Smart Parichaya Admin"
admin.site.site_title = "Smart Parichaya Admin"
admin.site.index_title = "Welcome to Smart Parichaya Admin Portal"


urlpatterns = [
    # Admin and Authentication (Optional: add allauth here if used)
    path('admin/', admin.site.urls),
    
    # Public Pages
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("blog/", views.blog, name="blog"),
    path("blog/<slug>", views.blogpost, name="blogpost"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
    
    # Auth System
    path("login/", views.loginSmartParichaya, name="loginSmartParichaya"),
    path("signup/", views.signupSmartparichaya, name="signupSmartParichaya"),
    path("logout/", views.logoutSmartParichaya, name="logoutSmartParichaya"),
    
    # Password Management
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-otp-for-password/", views.verify_otp_for_password, name="verify_otp_password"),
    path("reset-password/", views.reset_password, name="reset_password"),
    path("update-password/", views.update_password, name="update_password"),
    
    # Dashboard and Features
    path("testUserAuth/", RedirectView.as_view(url="/testUserAuth/dashboard/", permanent=True)),
    path("testUserAuth/dashboard/", views.dashboard, name="dashboard"),
    path("testUserAuth/cv-builder/", views.CvBuilder, name="cv-Builder"),
    path("testUserAuth/cv-editor/", views.cv_editor, name="cv_editor"),
    path("testUserAuth/coverletter/", views.coverLetter, name="coverletter"),
    path("testUserAuth/resume-score/", views.resumeScore, name="resume-score"),
    path("testUserAuth/jobs/", views.jobs, name="jobs"),
    
    # --- NEW: Job Application Path ---
    path("testUserAuth/apply/<int:job_id>/", views.apply_job, name="apply_job"),
    
    # Profile and Settings
    path("testUserAuth/feedback/", views.feedback, name="feedback"),
    path("testUserAuth/profile/", views.profile, name="profile"),
    path("testUserAuth/upload-profile-picture/", views.upload_profile_picture, name="upload_profile_picture"),
    path("testUserAuth/delete-profile-picture/", views.delete_profile_picture, name="delete_profile_picture"),
    path("update-username/", views.update_username, name="update_username"),
    path("change-password/", views.change_password, name="change_password"),
    
    # OTP/Verification
    path("send-verification-otp/", views.send_verification_otp, name="send_verification_otp"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("check-verification-status/", views.check_verification_status, name="check_verification_status"),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)