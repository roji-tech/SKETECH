from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
import logging
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_decode

from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator


from django.dispatch import receiver
from datetime import date

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from main import signals, utils
from main.utils import get_user_email
from main.email import ActivationEmail, ConfirmationEmail

User = get_user_model()


@receiver(signals.user_registered)
def send_verification_email_to_user(sender, user, request, **kwargs):
    context = {"user": user}
    to = [get_user_email(user)]
    ActivationEmail(request, context).send(to)
    # elif settings.SEND_CONFIRMATION_EMAIL:
    #     settings.EMAIL.confirmation(self.request, context).send(to)


# @receiver(post_save, sender=User)
# def send_verification_email(sender, instance, created, **kwargs):
#     user = instance
#     print(user)
#     if created and user.is_admin:
#         send_verification_email_to_user(user)


def activate_account(request, uidb64, token):
    context = {
        "site_url": "",
        "site_name": "SKE TECH"
    }
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and not user.is_active and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        context["user"] = user
        to = [get_user_email(user)]
        ConfirmationEmail(request, context).send(to)

        return render(request, "active.html", context)
    else:
        return render(request, "inactive.html", context)
