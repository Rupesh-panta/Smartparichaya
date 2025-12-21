# allauth_adapter.py
from allauth.account.adapter import DefaultAccountAdapter


class MyAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super(MyAccountAdapter, self).save_user(
            request, user, form, commit=False
        )
        # Ensure the user does not get admin privileges
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user
