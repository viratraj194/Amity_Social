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
    gender = models.CharField(max_length=20,null=True,blank=True,db_index=True)
    username = models.CharField(max_length=50, unique=True,db_index=True)
    # userSlug = models.SlugField(max_length=100,blank=True,unique=True)
    email = models.EmailField(max_length=100, unique=True,db_index=True)
    phone_number = models.CharField(max_length=12, blank=True,db_index=True)
    collage_name = models.CharField(blank=True,null=True,db_index=True)
    users_id = models.CharField(max_length=20,unique=True,db_index=True)
    agree_to_terms = models.BooleanField(default=False,db_index=True)
    is_approved = models.BooleanField(default=False,db_index=True)
    is_online = models.BooleanField(default=False,db_index=True)
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
    userBio = models.TextField(blank=True, null=True)
    cover_photo = models.ImageField(upload_to='users/cover_photo', blank=True, null=True,width_field='cover_width',height_field='cover_height')
    # cover photo width and height
    # user is privet 
    is_privet = models.BooleanField(default=False, db_index=True)

    cover_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    cover_height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    collage_pin_code = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    def save(self,*args, **kwargs):
        super().save(*args, **kwargs)
        



# follow system 
class Follower(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower} follows {self.following}'



class FollowRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='follow_requests_sent_from', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='follow_requests_sent_to', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f'{self.from_user} requests to follow {self.to_user}'




class Room(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True,db_index=True)
    slug = models.SlugField(unique=True, blank=True, null=True,db_index=True)
    participants = models.ManyToManyField(User, related_name='rooms',db_index=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rooms',db_index=True)
    is_private = models.BooleanField(default=False,db_index=True)
    is_group = models.BooleanField(default=False,db_index=True)
    description = models.TextField(blank=True, null=True,db_index=True)
    room_picture = models.ImageField(upload_to='room_pictures/', blank=True, null=True,db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or f'Room {self.id}'

    def get_active_users(self):
        """Get the list of active users in this room."""
        try:
            r = redis.Redis()  # Configure Redis if needed
            # Fetch online user IDs from Redis for this room
            online_user_ids = r.smembers(f'room:{self.slug}:users')
            # Convert bytes to integers and return as a list
            return list(map(int, online_user_ids))
        except redis.RedisError as e:
            logger.error(f"Error getting active users from Redis: {e}")
            return []

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def has_unread_messages(self, user):
        return self.messages.filter(receiver=user, read=False).exists()




class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =models.DateTimeField(auto_now=True)


    def __str__(self):
        return f'{self.sender} to {self.receiver}: {self.content}'

