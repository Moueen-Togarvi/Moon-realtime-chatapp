from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ChatRoom, Message, TypingIndicator, UserPresence, Notification


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User admin with additional fields"""
    list_display = ('username', 'email', 'phone_number', 'is_online', 'last_seen', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_online', 'created_at')
    search_fields = ('username', 'email', 'phone_number', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = list(UserAdmin.fieldsets) + [
        ('WhatsApp Profile', {
            'fields': ('phone_number', 'profile_picture', 'bio', 'is_online', 'last_seen')
        }),
    ]
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('WhatsApp Profile', {
            'fields': ('phone_number', 'profile_picture', 'bio')
        }),
    )


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    """ChatRoom admin interface"""
    list_display = ('name', 'room_type', 'created_by', 'participants_count', 'created_at', 'is_active')
    list_filter = ('room_type', 'is_active', 'created_at')
    search_fields = ('name', 'created_by__username')
    filter_horizontal = ('participants',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Message admin interface"""
    list_display = ('sender', 'room', 'content_preview', 'message_type', 'timestamp', 'is_read')
    list_filter = ('message_type', 'is_read', 'is_edited', 'timestamp')
    search_fields = ('sender__username', 'content', 'room__name')
    readonly_fields = ('id', 'timestamp', 'edited_at')
    filter_horizontal = ('read_by',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(TypingIndicator)
class TypingIndicatorAdmin(admin.ModelAdmin):
    """TypingIndicator admin interface"""
    list_display = ('user', 'room', 'is_typing', 'timestamp')
    list_filter = ('is_typing', 'timestamp')
    search_fields = ('user__username', 'room__name')


@admin.register(UserPresence)
class UserPresenceAdmin(admin.ModelAdmin):
    """UserPresence admin interface"""
    list_display = ('user', 'is_online', 'last_seen', 'status_message')
    list_filter = ('is_online', 'last_seen')
    search_fields = ('user__username', 'status_message')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification admin interface"""
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('id', 'created_at')
