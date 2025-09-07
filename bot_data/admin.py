from django.contrib import admin
from .models import Team, Player, SoloPlayer, SubscriptionChannel


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'captain', 'current_members_count', 'max_members', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'max_members']
    search_fields = ['name', 'captain__fullname']
    readonly_fields = ['referral_code', 'created_at']
    list_per_page = 20
    
    fieldsets = (
        ('Jamoa ma\'lumotlari', {
            'fields': ('name', 'captain', 'max_members')
        }),
        ('Referal', {
            'fields': ('referral_code',)
        }),
        ('Holat', {
            'fields': ('is_active', 'created_at')
        }),
    )


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['fullname', 'username', 'status', 'team', 'direction', 'created_at', 'is_active']
    list_filter = ['status', 'direction', 'is_active', 'created_at', 'team']
    search_fields = ['fullname', 'username', 'phone', 'freefire_id']
    readonly_fields = ['user_id', 'created_at', 'status']
    list_per_page = 20
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('fullname', 'birthdate', 'direction', 'phone')
        }),
        ('Free Fire', {
            'fields': ('freefire_id',)
        }),
        ('Telegram', {
            'fields': ('user_id', 'username')
        }),
        ('Jamoa va status', {
            'fields': ('team', 'status')
        }),
        ('Holat', {
            'fields': ('is_active', 'created_at')
        }),
    )


@admin.register(SoloPlayer)
class SoloPlayerAdmin(admin.ModelAdmin):
    list_display = ['player', 'looking_for_team']
    list_filter = ['looking_for_team']
    search_fields = ['player__fullname', 'player__username']
    
    fieldsets = (
        ('Solo o\'yinchi', {
            'fields': ('player', 'looking_for_team')
        }),
    )


@admin.register(SubscriptionChannel)
class SubscriptionChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel_type', 'is_required', 'is_active']
    list_filter = ['channel_type', 'is_required', 'is_active']
    search_fields = ['name', 'url']
    
    fieldsets = (
        ('Kanal ma\'lumotlari', {
            'fields': ('name', 'channel_type', 'url')
        }),
        ('Sozlamalar', {
            'fields': ('is_required', 'is_active')
        }),
    )