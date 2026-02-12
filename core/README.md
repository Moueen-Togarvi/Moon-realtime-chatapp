# WhatsApp Clone - Real-time Chat Application

A fully functional WhatsApp-like web application built with Django, Django Channels, WebSockets, and Tailwind CSS.

## 🚀 Features

### Core Chat Features
- **Real-time messaging** with WebSocket support
- **1-to-1 and group chats**
- **Message types**: Text, images, videos, audio, files, emojis
- **Message status**: Sent, delivered, read indicators
- **Typing indicators** - see when someone is typing
- **Online/Offline status** with last seen timestamps
- **Message replies** and editing capabilities
- **Unread message counters**

### User Management
- **User registration and authentication**
- **Profile management** with profile pictures and bio
- **User search** functionality
- **Online user discovery**

### Admin Features
- **Comprehensive admin panel** for user management
- **Message monitoring** and moderation
- **User activity tracking**
- **Chat room management**

### UI/UX Features
- **Responsive design** that works on all devices
- **Modern WhatsApp-like interface** with Tailwind CSS
- **Dark/Light theme support** (ready for implementation)
- **File upload** with drag-and-drop support
- **Emoji picker** integration ready
- **Browser notifications** for new messages

## 🛠️ Technology Stack

### Backend
- **Django 5.2.7** - Web framework
- **Django Channels** - WebSocket support for real-time features
- **SQLite** - Database (easily configurable for PostgreSQL/MySQL)
- **Pillow** - Image processing
- **Django Crispy Forms** - Form rendering

### Frontend
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript (Vanilla)** - Real-time WebSocket communication
- **HTML5** - Semantic markup
- **Responsive Design** - Mobile-first approach

### Real-time Features
- **WebSockets** - Real-time bidirectional communication
- **Django Channels** - WebSocket handling
- **In-memory Channel Layers** - Message broadcasting (Redis ready)

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd whatsapp-Clone/core
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 6: Run the Server with Daphne
```bash
daphne -p 8000 core.asgi:application
```

The application will be available at `http://localhost:8000`

## 🎯 Usage Guide

### For Users

1. **Registration/Login**
   - Visit `/register/` to create a new account
   - Visit `/login/` to sign in
   - Complete your profile with photo and bio

2. **Starting Chats**
   - Click on online users to start 1-to-1 chats
   - Use the search function to find users
   - Create group chats with multiple participants

3. **Messaging**
   - Send text messages instantly
   - Upload images and videos
   - See typing indicators
   - View message status (sent/delivered/read)

4. **Profile Management**
   - Update your profile information
   - Change profile picture
   - Set status messages

### For Administrators

1. **Admin Panel Access**
   - Visit `/admin/`
   - Login with superuser credentials
   - Manage users, chats, and messages

2. **User Management**
   - View all registered users
   - Monitor user activity
   - Manage user permissions

3. **Content Moderation**
   - Monitor all messages
   - Manage chat rooms
   - Handle user reports

## 🏗️ Project Structure

```
core/
├── app1/                    # Main Django app
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── forms.py            # Django forms
│   ├── consumers.py         # WebSocket consumers
│   ├── routing.py          # WebSocket routing
│   ├── urls.py             # URL patterns
│   ├── admin.py            # Admin configuration
│   └── templates/          # HTML templates
│       └── app1/
│           ├── base.html
│           ├── login.html
│           ├── register.html
│           ├── chat_list.html
│           ├── chat_room.html
│           ├── profile.html
│           ├── search_users.html
│           ├── create_group.html
│           └── notifications.html
├── core/                   # Django project settings
│   ├── settings.py         # Main settings
│   ├── urls.py            # Root URL configuration
│   ├── asgi.py            # ASGI configuration
│   └── wsgi.py            # WSGI configuration
├── static/                 # Static files (CSS, JS, images)
├── media/                  # User uploaded files
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file for production settings:

```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379/0
```

### Database Configuration
For production, update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Redis Configuration (Optional)
For production with Redis:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

## 🚀 Deployment

### Using Docker (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment
1. Set up a production server (Ubuntu/CentOS)
2. Install Python, PostgreSQL, Redis, Nginx
3. Configure environment variables
4. Run migrations and collect static files
5. Set up SSL certificates
6. Configure Nginx as reverse proxy

## 🔒 Security Features

- **CSRF Protection** - Cross-site request forgery protection
- **XSS Protection** - Cross-site scripting prevention
- **SQL Injection Protection** - Django ORM protection
- **File Upload Validation** - Type and size restrictions
- **User Authentication** - Secure login/logout
- **Session Management** - Secure session handling

## 📱 Mobile Responsiveness

The application is fully responsive and works on:
- **Desktop** - Full-featured experience
- **Tablet** - Optimized layout
- **Mobile** - Touch-friendly interface

## 🔮 Future Enhancements

### Planned Features
- **Voice Messages** - Record and send voice notes
- **Video Calls** - WebRTC integration
- **Message Encryption** - End-to-end encryption
- **Push Notifications** - Mobile app notifications
- **Message Reactions** - Emoji reactions to messages
- **Message Search** - Full-text search in messages
- **Chat Backup** - Export/import chat history
- **Themes** - Multiple UI themes
- **Multi-language Support** - Internationalization

### Technical Improvements
- **Caching** - Redis caching for better performance
- **CDN Integration** - Content delivery network
- **Load Balancing** - Multiple server instances
- **Monitoring** - Application performance monitoring
- **Testing** - Comprehensive test suite
- **CI/CD** - Automated deployment pipeline

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code comments

## 🎉 Acknowledgments

- Django team for the excellent framework
- Django Channels team for WebSocket support
- Tailwind CSS team for the utility-first CSS framework
- WhatsApp for the UI inspiration

---

**Built with ❤️ using Django + Channels + Tailwind CSS**
