from django.core.management.base import BaseCommand
from app1.models import User, ChatRoom, Message


class Command(BaseCommand):
    help = 'Create test data for WhatsApp clone'

    def handle(self, *args, **options):
        # Create test users
        user1, created = User.objects.get_or_create(
            username='testuser1',
            defaults={
                'email': 'testuser1@example.com',
                'first_name': 'Test',
                'last_name': 'User 1',
                'is_active': True
            }
        )
        if created:
            user1.set_password('testpass123')
            user1.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {user1.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'User already exists: {user1.username}'))

        user2, created = User.objects.get_or_create(
            username='testuser2',
            defaults={
                'email': 'testuser2@example.com',
                'first_name': 'Test',
                'last_name': 'User 2',
                'is_active': True
            }
        )
        if created:
            user2.set_password('testpass123')
            user2.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {user2.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'User already exists: {user2.username}'))

        # Create test chat room
        room = ChatRoom.objects.filter(
            room_type='direct',
            participants=user1
        ).filter(participants=user2).first()
        
        if not room:
            room = ChatRoom.objects.create(
                room_type='direct',
                created_by=user1
            )
            room.participants.add(user1, user2)
            self.stdout.write(self.style.SUCCESS(f'Created chat room: {room.id}'))
        else:
            self.stdout.write(self.style.WARNING(f'Chat room already exists: {room.id}'))

        # Create test messages
        if Message.objects.filter(room=room).count() == 0:
            Message.objects.create(
                sender=user1,
                room=room,
                content='Hello! This is a test message.',
                message_type='text'
            )
            Message.objects.create(
                sender=user2,
                room=room,
                content='Hi there! How are you?',
                message_type='text'
            )
            self.stdout.write(self.style.SUCCESS('Created test messages'))
        else:
            self.stdout.write(self.style.WARNING('Test messages already exist'))

        self.stdout.write(self.style.SUCCESS('Test data setup complete!'))
        self.stdout.write(f'Test users: {user1.username} / {user2.username} (password: testpass123)')
        self.stdout.write(f'Chat room ID: {room.id}')
