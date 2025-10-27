# 🔧 WebSocket Real-time Messaging Fix Guide

## ❌ Problem: Messages not sending, WebSocket keeps reconnecting

The issue is that you need to run the server with **ASGI (Daphne)** instead of the regular Django development server.

## ✅ Solution Steps:

### Step 1: Stop Current Server
```bash
# Stop any running Django servers
taskkill /f /im python.exe
```

### Step 2: Run with ASGI Server (Daphne)
```bash
cd D:\worksapace\whatsapp-Clone\core
daphne -b 127.0.0.1 -p 8000 core.asgi:application
```

### Step 3: Test WebSocket Connection
```bash
# Run the test script
python test_websocket.py
```

## 🧪 How to Test Real-time Messaging:

### Method 1: Browser Test
1. **Open 2 browser tabs**
2. **Tab 1**: Login as `testuser1` (password: `testpass123`)
3. **Tab 2**: Login as `testuser2` (password: `testpass123`)
4. **Both tabs**: Go to chat room `5070aad8-1f27-43f3-8827-2e66220782be`
5. **Send messages** - they should appear instantly!

### Method 2: WebSocket Test Page
1. Go to: http://localhost:8000/websocket-test/
2. Check if connection shows "Connected"

## 🔍 What to Look For:

### ✅ Success Indicators:
- **Green dot** in chat header = Connected
- **Console logs** show "WebSocket connection opened"
- **Messages appear instantly** without page refresh
- **No 404 errors** for `/ws/chat/...` URLs

### ❌ Error Indicators:
- **Red dot** = Disconnected
- **404 errors** for WebSocket URLs
- **"Connecting..." keeps showing**
- **Messages don't appear**

## 🐛 Common Issues & Fixes:

### Issue 1: "Not Found: /ws/chat/..."
**Cause**: Running regular Django server instead of Daphne
**Fix**: Use `daphne` command instead of `python manage.py runserver`

### Issue 2: "Port already in use"
**Cause**: Another server running on port 8000
**Fix**: 
```bash
taskkill /f /im python.exe
# Then restart with Daphne
```

### Issue 3: "WebSocket connection failed"
**Cause**: ASGI not properly configured
**Fix**: Check `core/asgi.py` file exists and is correct

### Issue 4: Messages not saving
**Cause**: Database issues or consumer errors
**Fix**: Check console logs for error messages

## 📱 Features That Should Work:

✅ **Real-time messaging** - No page refresh  
✅ **Typing indicators** - See when typing  
✅ **Online status** - Live presence updates  
✅ **Message status** - Sent/Delivered/Read  
✅ **File uploads** - Images and videos  
✅ **Group chats** - Multiple users  
✅ **Connection status** - Visual indicator  

## 🚀 Quick Commands:

```bash
# Start ASGI server (REQUIRED for WebSocket)
daphne -b 127.0.0.1 -p 8000 core.asgi:application

# Test WebSocket connection
python test_websocket.py

# Create test data
python manage.py create_test_data

# Check server logs
# Look for "WebSocket connection opened" messages
```

## 🎯 Expected Behavior:

1. **Open chat room** → Green dot appears
2. **Type message** → Shows "typing..." indicator
3. **Send message** → Appears instantly in both tabs
4. **No page refresh** needed
5. **Console shows** WebSocket activity

---

**Remember**: Always use `daphne` for WebSocket support, not `python manage.py runserver`!
