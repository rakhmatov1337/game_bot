from django.db import models
from django.utils import timezone
import uuid


class Team(models.Model):
    """Jamoa modeli"""
    name = models.CharField(max_length=100, verbose_name="Jamoa nomi")
    captain = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='captained_teams', verbose_name="Jamoa sardori")
    direction = models.CharField(max_length=100, default="Toshkent", verbose_name="Viloyat")
    referral_code = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="Referal kodi")
    max_members = models.IntegerField(default=4, verbose_name="Maksimal a'zolar soni")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Yaratilgan vaqt")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Jamoa"
        verbose_name_plural = "Jamoalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (Sardor: {self.captain.fullname})"

    @property
    def current_members_count(self):
        return self.members.count()

    @property
    def is_full(self):
        return self.current_members_count >= self.max_members
    
    @property
    def available_slots(self):
        return self.max_members - self.current_members_count


class Player(models.Model):
    """O'yinchi modeli"""
    REGISTRATION_TYPE_CHOICES = [
        ('solo', 'Solo'),
        ('team', 'Jamoa'),
    ]
    
    STATUS_CHOICES = [
        ('solo', 'Solo'),
        ('team_player', 'Jamoa o\'yinchisi'),
    ]

    fullname = models.CharField(max_length=255, verbose_name="To'liq ism")
    birthdate = models.CharField(max_length=10, verbose_name="Tug'ilgan sana")
    freefire_id = models.CharField(max_length=50, verbose_name="Free Fire ID")
    direction = models.CharField(max_length=100, verbose_name="Viloyat")
    phone = models.CharField(max_length=20, verbose_name="Telefon raqam")
    user_id = models.BigIntegerField(unique=True, verbose_name="Telegram User ID")
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Username")
    registration_type = models.CharField(max_length=10, choices=REGISTRATION_TYPE_CHOICES, verbose_name="Ro'yxatdan o'tish turi")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='solo', verbose_name="Status")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='members', verbose_name="Jamoa")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Yaratilgan vaqt")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "O'yinchi"
        verbose_name_plural = "O'yinchilar"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Statusni avtomatik o'rnatish
        if self.team:
            self.status = 'team_player'
        else:
            self.status = 'solo'
        super().save(*args, **kwargs)

    def __str__(self):
        username_display = self.username or "username yo'q"
        return f"{self.fullname} (@{username_display}) - {self.get_status_display()}"

    def can_remove_from_team(self, captain_user_id):
        """O'yinchini jamoadan chiqarish mumkinligini tekshirish"""
        return self.team and self.team.captain.user_id == captain_user_id


class SoloPlayer(models.Model):
    """Solo o'yinchilar uchun alohida model"""
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='solo_profile', verbose_name="O'yinchi")
    looking_for_team = models.BooleanField(default=True, verbose_name="Jamoa qidirayapti")

    class Meta:
        verbose_name = "Solo o'yinchi"
        verbose_name_plural = "Solo o'yinchilar"

    def __str__(self):
        return f"Solo: {self.player.fullname}"


class SubscriptionChannel(models.Model):
    """Obuna kanallari uchun model"""
    name = models.CharField(max_length=100, verbose_name="Kanal nomi")
    channel_type = models.CharField(
        max_length=20,
        choices=[
            ('telegram', 'Telegram'),
            ('youtube', 'YouTube'),
            ('instagram', 'Instagram')
        ],
        verbose_name="Kanal turi"
    )
    url = models.URLField(verbose_name="Havola")
    is_required = models.BooleanField(default=True, verbose_name="Majburiy")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Obuna kanali"
        verbose_name_plural = "Obuna kanallari"

    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"