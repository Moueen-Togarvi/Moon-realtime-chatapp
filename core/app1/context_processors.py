from .models import Notification

def notifications_context(request):
    if request.user.is_authenticated:
        return {
            'notifications': Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
        }
    return {}
