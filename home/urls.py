from django.contrib import admin
from django.urls import path, include
from home import views
from django.conf import settings
from django.conf.urls.static import static
from home import views
from django.views.generic import RedirectView


admin.site.site_header = "Simpfolio Admin"  # Header of the login form
admin.site.site_title = "Simpfolio Admin"  # <title> of the page
# The welcome heading after logging in to the admin portal
admin.site.index_title = "Welcome to Simfolio Admin Portal"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("blog/", views.blog, name="blog"),
    path("blog/<slug>", views.blogpost, name="blogpost"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
    path("login/", views.loginSimpfolio, name="loginSimpfolio"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("logout/", views.logoutSimpfolio, name="logoutSimpfolio"),
    path("signup/", views.signupSimpfolio, name="signupSimpfolio"),
    path(
        "testUserAuth/",
        RedirectView.as_view(url="/testUserAuth/dashboard/", permanent=True),
    ),
    path("testUserAuth/dashboard/", views.dashboard, name="dashboard"),
    path("testUserAuth/cv-builder/", views.CvBuilder, name="cv-Builder"),
    path("testUserAuth/coverletter/", views.coverLetter, name="coverletter"),
    path("testUserAuth/resume-score/", views.resumeScore, name="resume-score"),
    path("testUserAuth/jobs/", views.jobs, name="jobs"),
    path("testUserAuth/feedback/", views.feedback, name="feedback"),
    path("testUserAuth/profile/", views.profile, name="profile"),
    path(
        "testUserAuth/upload-profile-picture/",
        views.upload_profile_picture,
        name="upload_profile_picture",
    ),
    path(
        "testUserAuth/delete-profile-picture/",
        views.delete_profile_picture,
        name="delete_profile_picture",
    ),
    path("update-username/", views.update_username, name="update_username"),
    path("change-password/", views.change_password, name="change_password"),
    path(
        "send-verification-otp/",
        views.send_verification_otp,
        name="send_verification_otp",
    ),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path(
        "check-verification-status/",
        views.check_verification_status,
        name="check_verification_status",
    ),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-otp-for-password/", views.verify_otp_for_password, name="verify_otp"),
    path("reset-password/", views.reset_password, name="reset_password"),
    path("update-password/", views.update_password, name="update_password"),
    path("cv-editor/", views.cv_editor, name="cv_editor"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
