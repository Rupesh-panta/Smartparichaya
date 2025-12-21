from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Override the DefaultSocialAccountAdapter from allauth in order to associate
    the social account with a matching User automatically, skipping the email
    confirm form and existing email error
    """

    def pre_social_login(self, request, sociallogin):
        user = User.objects.filter(email=sociallogin.user.email).first()
        if user and not sociallogin.is_existing:
            sociallogin.connect(request, user)
        elif not user:  # New user creation
            self.send_welcome_email(sociallogin.user)

    def send_welcome_email(self, social_user):
        email = social_user.email
        username = (
            social_user.first_name or social_user.username
        )  # Get user's name from social account

        logger.info(f"Sending welcome email to {email}")

        subject = "Welcome to Simpfolio!"
        message = (
            f"Hi {username},\n\n"
            "Thank you for registering at Simpfolio. We are excited to help you craft your best resumes and test your CV score!\n\n"
            "Feel free to explore our platform, and reach out if you have any questions.\n\n"
            "Best regards,\n"
            "The Simpfolio Team"
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            logger.info(f"Welcome email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
