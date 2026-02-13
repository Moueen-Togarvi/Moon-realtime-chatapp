import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from app1.models import User, ChatRoom

def fix_ai_presence():
    try:
        ai_user = User.objects.get(username='AI_Assistant')
    except User.DoesNotExist:
        print("AI_Assistant user does not exist.")
        return

    print(f"Checking rooms for AI_Assistant (ID: {ai_user.id})...")
    
    # Find all rooms where AI is a participant
    ai_rooms = ChatRoom.objects.filter(participants=ai_user)
    
    for room in ai_rooms:
        participants = list(room.participants.all())
        count = len(participants)
        is_direct = room.room_type == 'direct'
        
        # Condition for invalid presence:
        # 1. Direct chat with != 2 participants (e.g., 3 people including AI)
        # 2. Group chat (AI shouldn't be in group chats based on current logic)
        
        if is_direct and count == 2:
            # This is likely a valid AI chat (User + AI)
            # Double check that the other user isn't also AI (weird edge case)
            continue
        
        print(f"Removing AI from Room {room.id}: Type={room.room_type}, Count={count}")
        room.participants.remove(ai_user)
        print("  -> Removed.")

    print("Fix complete.")

if __name__ == "__main__":
    fix_ai_presence()
