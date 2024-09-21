from django.contrib.auth.models import AbstractUser
from django.db import models
#from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import static
import os

def user_avatar_path(instance, filename):
    return f'users/{instance.id}/avatar/{filename}'

def default_avatar_path():
    return ''

class FriendshipStatus(models.TextChoices):
    PENDING = 'PE', 'Pending'
    ACCEPTED = 'AC', 'Accepted'

class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to=user_avatar_path, null=True, blank=True)
    nickname = models.CharField(max_length=30, unique=True, null=True, blank=True)
    friends = models.ManyToManyField(
        'self',
        through='Friendship',
        symmetrical=False,
        related_name="friended_by"
    )

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        else:
            return static('images/default_avatar.png')

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = CustomUser.objects.get(pk=self.pk)
                if old_instance.avatar and self.avatar != old_instance.avatar and old_instance.avatar.name:
                    old_avatar_path = os.path.join(settings.MEDIA_ROOT, old_instance.avatar.name)
                    if os.path.isfile(old_avatar_path):
                        os.remove(old_avatar_path)
                        print(f"Deleted old avatar: {old_avatar_path}")
            except CustomUser.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.avatar:
            avatar_path = os.path.join(settings.MEDIA_ROOT, self.avatar.name)
            if os.path.isfile(avatar_path):
                os.remove(avatar_path)
                print(f"Deleted avatar during user deletion: {avatar_path}")
        super().delete(*args, **kwargs)

    def send_friend_request(self, to_user):
        if (to_user != self):
            Friendship.objects.get_or_create(
                from_user=self,
                to_user=to_user,
                defaults={'status': FriendshipStatus.PENDING}
            )

    def accept_friend_request(self, from_user):
        if (to_user != self):
            friendship = Friendship.objects.filter(
                from_user=from_user,
                to_user=self,
                status=FriendshipStatus.PENDING
            ).first()
            if friendship:
                friendship.status = FriendshipStatus.ACCEPTED
                friendship.save()

    def reject_friend_request(self, from_user):
        if (to_user != self):
            Friendship.objects.filter(
                from_user=from_user,
                to_user=self,
                status=FriendshipStatus.PENDING
            ).delete()

    def remove_friend_from_list(self, friend):
        Friendship.objects.filter(
            (models.Q(from_user=self, to_user=friend) |
             models.Q(from_user=friend, to_user=self)),
            status=FriendshipStatus.ACCEPTED
        ).delete()

    def get_friends(self):
        return CustomUser.objects.filter(
            models.Q(friendships_sent__from_user=self, friendships_sent__status=FriendshipStatus.ACCEPTED) |
            models.Q(friendships_received__to_user=self, friendships_received__status=FriendshipStatus.ACCEPTED)
        ).distinct()

    def get_pending_friends_request(self):
        return CustomUser.objects.filter(
            friendships_sent__to_user=self,
            friendships_sent__status=FriendshipStatus.PENDING
        )

class Friendship(models.Model):
    from_user = models.ForeignKey(CustomUser, related_name='friendships_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(CustomUser, related_name='friendships_received', on_delete=models.CASCADE)
    status = models.CharField(max_length=2, choices=FriendshipStatus.choices, default=FriendshipStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ( 'from_user', 'to_user')


