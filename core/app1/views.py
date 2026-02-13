from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Max, Case, When, IntegerField
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import logging
import json
import uuid
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from .models import User, ChatRoom, Message, Notification, UserPresence
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
 


def home(request):
    """Home page - redirect to chat if authenticated, otherwise to login"""
    if request.user.is_authenticated:
        return redirect('chat_list')
    return redirect('public_home')


def public_home(request):
    return render(request, 'app1/public_home.html')


def public_features(request):
    return render(request, 'app1/public_features.html')


def public_about(request):
    return render(request, 'app1/public_about.html')


def public_contact(request):
    return render(request, 'app1/public_contact.html')


def public_tools(request):
    return render(request, 'app1/public_tools.html')


def public_integrations(request):
    return render(request, 'app1/public_integrations.html')


def public_use_cases(request):
    return render(request, 'app1/public_use_cases.html')


def public_ai(request):
    return render(request, 'app1/public_ai.html')


@login_required
def chat_list(request):
    """Display list of chat rooms for the current user"""
    # Ensure the user has a chat room with the AI assistant
    try:
        ai_user, _ = User.objects.get_or_create(
            username='AI_Assistant',
            defaults={
                'first_name': 'AI',
                'last_name': 'Assistant',
                'is_active': True,
                'email': 'ai@example.com'
            }
        )
        
        # Check if a direct chat already exists between user and AI
        existing_ai_room = ChatRoom.objects.filter(
            room_type='direct',
            participants__id=request.user.id
        ).filter(participants__id=ai_user.id).distinct().first()
        
        if not existing_ai_room:
            # Create a direct chat room between the user and AI assistant
            ai_room = ChatRoom.objects.create(
                room_type='direct',
                created_by=ai_user
            )
            ai_room.participants.add(request.user, ai_user)
    except Exception as e:
        # Log the error but continue
        print(f"Error ensuring AI chat room: {e}")
    
    chat_rooms = ChatRoom.objects.filter(
        participants__id=request.user.id,
        is_active=True
    ).distinct().annotate(
        last_message_time=Max('messages__timestamp'),
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)),
    ).order_by('-last_message_time', '-updated_at')
    
    # Add is_ai_room attribute to each room
    ai_user = User.objects.get(username='AI_Assistant')
    for room in chat_rooms:
        room.is_ai_room = False
        if room.room_type == 'direct' and room.participants.count() == 2:
            participant_usernames = [p.username for p in room.participants.all()]
            if 'AI_Assistant' in participant_usernames:
                room.is_ai_room = True

    online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    # Get the AI room separately to avoid duplicates
    ai_room = None
    regular_rooms = []
    for room in chat_rooms:
        if room.is_ai_room and ai_room is None:
            ai_room = room
        elif not room.is_ai_room:
            regular_rooms.append(room)
    
    context = {
        'chat_rooms': regular_rooms,
        'ai_room': ai_room,
        'online_users': online_users,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'app1/chat_list.html', context)


@login_required
def chat_room(request, room_id):
    """Display specific chat room"""
    room = get_object_or_404(
        ChatRoom.objects.filter(participants__id=request.user.id, is_active=True).distinct(),
        id=room_id
    )
    if request.user not in room.participants.all():
        messages.error(request, 'You do not have access to this chat room.')
        return redirect('chat_list')

    messages_qs = Message.objects.filter(room=room).order_by('timestamp')

    unread_messages = Message.objects.filter(
        room=room,
        is_read=False
    ).exclude(sender=request.user)
    for message in unread_messages:
        message.read_by.add(request.user)
        message.is_read = True
        message.save()

    Notification.objects.filter(
        user=request.user, 
        related_room=room, 
        is_read=False
    ).update(is_read=True)

    other_participants = room.participants.exclude(id=request.user.id)

    # Check if current room is an AI room
    is_ai_room = False
    try:
        ai_user = User.objects.get(username='AI_Assistant')
        if room.room_type == 'direct' and room.participants.count() == 2:
            participant_usernames = [p.username for p in room.participants.all()]
            if 'AI_Assistant' in participant_usernames:
                is_ai_room = True
    except User.DoesNotExist:
        # AI user doesn't exist yet
        pass

    chat_rooms = ChatRoom.objects.filter(
        participants__id=request.user.id,
        is_active=True
    ).distinct().annotate(
        last_message_time=Max('messages__timestamp'),
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)),
    ).order_by('-last_message_time', '-updated_at')
    
    # Add is_ai_room attribute to each room
    try:
        ai_user = User.objects.get(username='AI_Assistant')
        for room in chat_rooms:
            room.is_ai_room = False
            if room.room_type == 'direct' and room.participants.count() == 2:
                participant_usernames = [p.username for p in room.participants.all()]
                if 'AI_Assistant' in participant_usernames:
                    room.is_ai_room = True
    except User.DoesNotExist:
        # AI user doesn't exist yet, so no rooms are AI rooms
        pass

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)

    # Get the AI room separately to avoid duplicates matching chat_list logic
    ai_room = None
    regular_rooms = []
    for room in chat_rooms:
        if room.is_ai_room and ai_room is None:
            ai_room = room
        elif not room.is_ai_room:
            regular_rooms.append(room)

    context = {
        'room': room,
        'messages': messages_qs,
        'other_participants': other_participants,
        'chat_rooms': regular_rooms,
        'ai_room': ai_room,
        'online_users': online_users,
        'is_ai_room': is_ai_room,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'app1/chat_room.html', context)


@login_required
def create_chat(request, user_id):
    """Create a new chat room with another user"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if a direct chat already exists (strict filtering)
    existing_room = ChatRoom.objects.filter(
        room_type='direct',
        participants__id=request.user.id
    ).filter(participants__id=other_user.id).distinct().first()
    
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
            
            # Ensure current user (admin) isn't re-added and skip invalid IDs
            for user_id in participant_ids:
                if str(user_id) == str(request.user.id):
                    continue
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
            
            # Create a default chat room with the AI assistant
            try:
                # Get or create the AI assistant user
                ai_user, _ = User.objects.get_or_create(
                    username='AI_Assistant',
                    defaults={
                        'first_name': 'AI',
                        'last_name': 'Assistant',
                        'is_active': True,
                        'email': 'ai@example.com'
                    }
                )
                
                # Create a direct chat room between the new user and AI assistant
                ai_room = ChatRoom.objects.create(
                    room_type='direct',
                    created_by=ai_user
                )
                ai_room.participants.add(user, ai_user)
                
            except Exception as e:
                # Log the error but don't fail registration
                print(f"Error creating AI chat room: {e}")
            
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


@require_http_methods(["POST"])
@csrf_exempt
def ai_reply(request):
    """Simple AI reply endpoint backing public AI page and hooks.
    Accepts JSON {"prompt": str} or form-data with field 'text'. Returns {"reply": str}.
    """
    try:
        # Extract prompt from JSON or form-data
        prompt = None
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = json.loads(request.body.decode('utf-8')) if request.body else {}
            except json.JSONDecodeError:
                body = {}
            prompt = (body.get('prompt') or '').strip()
        if not prompt:
            prompt = (request.POST.get('text') or '').strip()

        if not prompt:
            return JsonResponse({'error': 'Missing prompt'}, status=400)

        # Use Gemini via google-generativeai if configured
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        model_name = getattr(settings, 'GEMINI_MODEL', None) or 'gemini-flash-latest'

        reply_text = None
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                
                # Updated model candidates with working model names
                model_candidates = []
                seen = set()
                for name in [model_name, 'gemini-flash-latest', 'gemini-2.0-flash', 'gemini-pro-latest']:
                    if name and name not in seen:
                        model_candidates.append(name)
                        seen.add(name)

                last_err = None
                for candidate in model_candidates:
                    try:
                        model = genai.GenerativeModel(candidate)
                        result = model.generate_content(prompt)
                        # Robust extraction
                        text_candidate = None
                        try:
                            text_candidate = getattr(result, 'text', None)
                        except Exception:
                            text_candidate = None
                        if not text_candidate:
                            try:
                                if hasattr(result, 'candidates') and result.candidates:
                                    for c in result.candidates:
                                        content_obj = getattr(c, 'content', None)
                                        parts = getattr(content_obj, 'parts', []) if content_obj else []
                                        for p in parts:
                                            t = getattr(p, 'text', None) or (str(p) if p is not None else None)
                                            if t and t.strip():
                                                text_candidate = t
                                                break
                                        if text_candidate:
                                            break
                            except Exception:
                                pass
                        reply_text = (text_candidate or '').strip() or None
                        if reply_text:
                            break
                    except Exception as e:
                        last_err = e
                        continue

                if not reply_text and last_err is not None:
                    logging.exception("Gemini provider error while generating content")
                    if getattr(settings, 'DEBUG', False):
                        reply_text = f"AI provider error: {str(last_err)[:180]}"
                    else:
                        reply_text = "AI provider error. Please try again later."
            except Exception as e:
                logging.exception("Gemini initialization error")
                if getattr(settings, 'DEBUG', False):
                    reply_text = f"AI init error: {str(e)[:180]}"
                else:
                    reply_text = "AI initialization error."

        if not reply_text:
            # Graceful fallback if no provider configured
            reply_text = "AI is not configured. Set GEMINI_API_KEY in .env."

        # If room_id provided, post AI reply into that room and broadcast
        room_id = None
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = json.loads(request.body.decode('utf-8')) if request.body else {}
            except json.JSONDecodeError:
                body = {}
            room_id = body.get('room_id') or body.get('room')
        if not room_id:
            room_id = request.POST.get('room_id')

        if room_id:
            try:
                # Validate user context and room membership when posting into a room
                if not request.user.is_authenticated:
                    return JsonResponse({'reply': reply_text})

                room = ChatRoom.objects.get(id=room_id)
                if not room.participants.filter(id=request.user.id).exists():
                    return JsonResponse({'reply': reply_text})

                # Getting AI User
                ai_user, _ = User.objects.get_or_create(
                    username='AI_Assistant',
                    defaults={
                        'first_name': 'AI',
                        'last_name': 'Assistant',
                        'is_active': True,
                    }
                )

                # IMPORTANT FIX: Do not add AI to existing human-to-human rooms
                # Only add if AI is ALREADY a participant, or if room is empty (which shouldn't happen here really)
                # Or if the room was explicitly created for AI.
                # Here we simply check: Is AI already in the room?
                if not room.participants.filter(id=ai_user.id).exists():
                    # If this is a direct chat with 2 people (Human + Human), adding AI makes it 3.
                    # We should BLOCK adding AI here.
                    # The only case we might add AI is if the user is alone in the room?
                    if room.participants.count() >= 2:
                         # Human-Human chat. Do NOT intrude.
                         # We can return the reply as JSON but NOT post it to the room.
                         return JsonResponse({'reply': reply_text})

                # Ensure AI is participant (safe now)
                if not room.participants.filter(id=ai_user.id).exists():
                    room.participants.add(ai_user)

                # Create message
                ai_message = Message.objects.create(
                    sender=ai_user,
                    room=room,
                    content=reply_text,
                    message_type='text'
                )

                # Serialize minimal shape expected by frontend addMessage()
                serialized = {
                    'id': str(ai_message.id),
                    'sender': {
                        'id': str(ai_user.id),
                        'username': ai_user.username,
                        'profile_picture': ai_user.profile_picture.url if getattr(ai_user, 'profile_picture', None) else None
                    },
                    'content': ai_message.content,
                    'message_type': ai_message.message_type,
                    'media_file': ai_message.media_file.url if ai_message.media_file else None,
                    'timestamp': ai_message.timestamp.isoformat(),
                    'is_read': ai_message.is_read,
                    'reply_to': str(ai_message.reply_to.id) if ai_message.reply_to else None,
                }

                # Broadcast to room via Channels
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'chat_{room.id}',
                    {
                        'type': 'chat_message',
                        'message': serialized,
                    }
                )
            except Exception:
                # Don't fail the API response if room broadcast has issues
                pass

        return JsonResponse({'reply': reply_text})
    except Exception as e:
        return JsonResponse({'error': 'Server error', 'details': str(e)[:200]}, status=500)




 
