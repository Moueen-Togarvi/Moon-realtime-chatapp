# Quick Start Guide - WhatsApp Clone

## 🚀 Get Started in 5 Minutes

### 1. Navigate to the Project Directory
```bash
cd D:\worksapace\whatsapp-Clone\core
```

### 2. Activate Virtual Environment
```bash
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies (if not already installed)
```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
python manage.py migrate
```

### 5. Start the Development Server
```bash
python manage.py runserver
```

### 6. Access the Application
- **Main App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
  - Username: `admin`
  - Password: `admin123`

## 🎯 Test the Features

### Create Test Users
1. Go to http://localhost:8000/register
2. Create 2-3 test accounts
3. Login with different accounts in different browser tabs/windows

### Test Real-time Chat
1. Login with User A
2. Open another browser tab/window and login with User B
3. Start a chat between them
4. Send messages and see them appear instantly
5. Test typing indicators
6. Upload images/videos

### Test Group Chats
1. Create a group chat with multiple users
2. Test group messaging
3. Test online/offline status

## 🔧 Admin Features

### Access Admin Panel
1. Go to http://localhost:8000/admin
2. Login with admin credentials
3. Explore user management, chat rooms, and messages

### Admin Capabilities
- View all users and their activity
- Monitor all messages
- Manage chat rooms
- Track user presence and online status

## 📱 Mobile Testing

### Test Responsive Design
1. Open browser developer tools (F12)
2. Switch to mobile view
3. Test the chat interface on different screen sizes
4. Verify touch interactions work properly

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
- Check if port 8000 is available
- Ensure all dependencies are installed
- Verify Python version (3.8+)

**WebSocket connection fails:**
- Check browser console for errors
- Ensure Django Channels is properly installed
- Verify ASGI configuration

**Database errors:**
- Run `python manage.py migrate` again
- Check database permissions
- Verify database file exists

**Static files not loading:**
- Run `python manage.py collectstatic`
- Check STATIC_URL setting
- Verify static files directory exists

### Getting Help
- Check the main README.md for detailed documentation
- Review Django and Channels documentation
- Check browser console for JavaScript errors
- Verify all dependencies are correctly installed

## 🎉 You're Ready!

Your WhatsApp clone is now running with:
- ✅ Real-time messaging
- ✅ User authentication
- ✅ File uploads
- ✅ Admin panel
- ✅ Responsive design
- ✅ Online/offline status
- ✅ Typing indicators

Enjoy testing your new chat application! 🚀
