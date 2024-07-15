from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .utils import send_notification_email

class UserManager(BaseUserManager):
    def create_user(self,first_name,last_name,username,email,password=None):
        if not email:
            raise ValueError('User must have a email address.')
        if not username: 
            raise ValueError('User must have a Username')
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name= first_name,
            last_name = last_name,

        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self,first_name,last_name,username,email,password=None):
        user = self.create_user(
            email = self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password
        )
        user.is_admin =True
        user.is_staff = True
        user.is_active = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=20,null=True,blank=True)
    username = models.CharField(max_length=50, unique=True)
    user_slug = models.SlugField(max_length=100,unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=12, blank=True)
    id_card_number = models.CharField(max_length=15,blank=True)
    users_id = models.CharField(max_length=20,blank=True,null=True)
    id_card_image = models.ImageField(upload_to='users/id_card_image')
    agree_to_terms = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    
    # REQUIRED_FIELDS 
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    
    def save(self, *args, **kwargs):
        if self.pk is not None:
            # UPDATE
            orig = User.objects.get(pk=self.pk)
            if orig.is_approved != self.is_approved:
                context = {
                    'user': orig,
                    'is_approved': self.is_approved,
                    'to_email': orig.email
                }
                if self.is_approved:
                    # send notification email for approval
                    mail_subject = 'Congratulations, your account is approved for the post'
                    mail_template = 'accounts/email/admin_approval_email.html'
                    send_notification_email(mail_subject, mail_template, context)
                else:
                    # send notification email for disapproval
                    mail_subject = 'Sorry, your account is not approved for the post'
                    mail_template = 'accounts/email/admin_approval_email.html'
                    send_notification_email(mail_subject, mail_template, context)
        return super(User, self).save(*args, **kwargs)







class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='users/profile_picture', blank=True, null=True,width_field='image_width',height_field='image_height')
    # profile picture  width and height 
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)

    cover_photo = models.ImageField(upload_to='users/cover_photo', blank=True, null=True,width_field='cover_width',height_field='cover_height')
    # cover photo width and height 
    cover_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    cover_height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    collage_name = models.CharField(max_length=50,blank=True,null=True)
    collage_pin_code = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    def save(self,*args, **kwargs):
        super().save(*args, **kwargs)
        if self.profile_picture:
            print(f'profile picture height: {self.profile_picture.height}')
            print(f'Profile picture width: {self.profile_picture.width}')
        if self.cover_photo:
            print(f'Cover photo height: {self.cover_photo.height}')
            print(f'Cover photo width: {self.cover_photo.width}')

    