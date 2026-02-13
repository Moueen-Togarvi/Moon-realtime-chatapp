import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from app1.models import User, ChatRoom

def check_ai_presence():
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
        names = [p.username for p in participants]
        is_direct = room.room_type == 'direct'
        count = len(participants)
        
        print(f"Room {room.id}: Type={room.room_type}, Count={count}, Participants={names}")
        
        if is_direct and count == 2:
            print("  -> Valid AI Direct Chat")
        else:
            print("  -> INVALID/UNEXPECTED AI PRESENCE! AI should only be in direct chats with 2 ppl.")
            # Verify if this is the "conflict"
            
    print("Check complete.")

if __name__ == "__main__":
    check_ai_presence()
