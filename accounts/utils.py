import datetime
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

def users_id_generator(user_id):
    current_datetime = datetime.datetime.now().strftime('%Y%m%d%H%M%S')#202212281059 
    users_id = current_datetime + str(user_id)
    print(users_id)
    return users_id


def detectUser(user):
    if user.is_superadmin:
        redirectUrl = '/super_admin/'
        return redirectUrl
    else:
        redirectUrl = 'UserDashboard'
        return redirectUrl



def send_email_verification(request,user,mail_subject,mail_template):
    from_mail = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    message = render_to_string(mail_template,{
        'user':user,
        'domain':current_site,
        'uid':urlsafe_base64_encode(force_bytes(user.pk)),
        'token':default_token_generator.make_token(user)
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_mail, to=[to_email])
    mail.content_subtype = "html"
    mail.send()


def send_notification_email(mail_subjects, mail_template, context):
    from_email = settings.DEFAULT_FROM_EMAIL
    message = render_to_string(mail_template, context)
    if(isinstance(context['to_email'],str)):
        to_email = []
        to_email.append(context['to_email'])
    else:      
        to_email = context['to_email']
    mail = EmailMessage(mail_subjects, message, from_email, to=to_email)
    mail.content_subtype = "html"
    # mail.attach(context['image'])
    mail.send()
    return



