from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import uuid
from .models import User, ChatRoom, Message, Notification, UserPresence
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm


def home(request):
    """Home page - redirect to chat if authenticated, otherwise to login"""
    if request.user.is_authenticated:
        return redirect('chat_list')
    return redirect('login')


@login_required
def chat_list(request):
    """Display list of chat rooms for the current user"""
    # Get all chat rooms for the current user
    chat_rooms = ChatRoom.objects.filter(
        participants=request.user,
        is_active=True
    ).annotate(
        last_message_time=Max('messages__timestamp'),
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    ).order_by('-last_message_time', '-updated_at')

    # Get online users for creating new chats
    online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)

    # Get unread notifications count
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'chat_rooms': chat_rooms,
        'online_users': online_users,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'app1/chat_list.html', context)


@login_required
def chat_room(request, room_id):
    """Display specific chat room"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    
    # Get messages for this room
    messages = Message.objects.filter(room=room).order_by('timestamp')
    
    # Mark messages as read
    unread_messages = Message.objects.filter(
        room=room,
        is_read=False
    ).exclude(sender=request.user)
    
    for message in unread_messages:
        message.read_by.add(request.user)
        message.is_read = True
        message.save()

    # Mark notifications as read for this room
    Notification.objects.filter(
        user=request.user, 
        related_room=room, 
        is_read=False
    ).update(is_read=True)

    # Get other participants
    other_participants = room.participants.exclude(id=request.user.id)

    context = {
        'room': room,
        'messages': messages,
        'other_participants': other_participants,
    }
    return render(request, 'app1/chat_room.html', context)


@login_required
def create_chat(request, user_id):
    """Create a new chat room with another user"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if a direct chat already exists
    existing_room = ChatRoom.objects.filter(
        room_type='direct',
        participants=request.user
    ).filter(participants=other_user).first()
    
    if existing_room:
        return redirect('chat_room', room_id=existing_room.id)
    
    # Create new chat room
    room = ChatRoom.objects.create(
        room_type='direct',
        created_by=request.user
    )
    room.participants.add(request.user, other_user)
    
    return redirect('chat_room', room_id=room.id)


@login_required
def create_group_chat(request):
    """Create a new group chat"""
    if request.method == 'POST':
        name = request.POST.get('name')
        participant_ids = request.POST.getlist('participants')
        
        if name and participant_ids:
            room = ChatRoom.objects.create(
                name=name,
                room_type='group',
                created_by=request.user
            )
            room.participants.add(request.user)
            
            for user_id in participant_ids:
                try:
                    user = User.objects.get(id=user_id)
                    room.participants.add(user)
                except User.DoesNotExist:
                    pass
            
            return redirect('chat_room', room_id=room.id)
    
    # Get all users except current user
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'app1/create_group.html', {'users': users})


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('chat_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'app1/register.html', {'form': form})


def user_login(request):
    """User login"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                # Update user presence
                presence, created = UserPresence.objects.get_or_create(user=user)
                presence.is_online = True
                presence.last_seen = timezone.now()
                presence.save()
                
                user.is_online = True
                user.last_seen = timezone.now()
                user.save()
                
                messages.success(request, 'Welcome back!')
                return redirect('chat_list')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'app1/login.html', {'form': form})


@login_required
def user_logout(request):
    """User logout"""
    # Update user presence
    presence, created = UserPresence.objects.get_or_create(user=request.user)
    presence.is_online = False
    presence.last_seen = timezone.now()
    presence.save()
    
    request.user.is_online = False
    request.user.last_seen = timezone.now()
    request.user.save()
    
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def profile(request):
    """User profile page"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'app1/profile.html', {'form': form})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def upload_media(request):
    """Handle media file uploads"""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    
    # Validate file type and size
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/webm']
    if file.content_type not in allowed_types:
        return JsonResponse({'error': 'Invalid file type'}, status=400)
    
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        return JsonResponse({'error': 'File too large'}, status=400)
    
    # Save file
    filename = f"{uuid.uuid4()}_{file.name}"
    file_path = default_storage.save(f'chat_media/{filename}', ContentFile(file.read()))
    
    return JsonResponse({
        'success': True,
        'file_url': default_storage.url(file_path),
        'file_name': filename
    })


@login_required
def notifications(request):
    """Display user notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark notifications as read
    unread_notifications = notifications.filter(is_read=False)
    for notification in unread_notifications:
        notification.is_read = True
        notification.save()
    
    return render(request, 'app1/notifications.html', {'notifications': notifications})


@login_required
def search_users(request):
    """Search for users to start a chat"""
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).exclude(id=request.user.id)[:10]
    else:
        users = User.objects.exclude(id=request.user.id)[:10]
    
    return render(request, 'app1/search_users.html', {'users': users, 'query': query})


def websocket_test(request):
    """Test WebSocket connectivity"""
    return render(request, 'app1/websocket_test.html')
