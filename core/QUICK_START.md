# WhatsApp Clone - Quick Start Commands

## Start the Server

```bash
cd D:\worksapace\whatsapp-Clone\core
daphne -b 127.0.0.1 -p 8000 core.asgi:application
```

## Stop the Server

```bash
taskkill /f /im python.exe
```

## Access URLs

- Home: http://localhost:8000/
- Login: http://localhost:8000/login
- Chats: http://localhost:8000/chats/
- Admin: http://localhost:8000/admin/

## Test Users

### User 1
- Username: `testuser1`
- Password: `testpass123`

### User 2
- Username: `testuser2`
- Password: `testpass123`

## Setup Commands (First Time Only)

### Install Dependencies
```bash
cd D:\worksapace\whatsapp-Clone\core
pip install -r requirements.txt
```

### Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Test Data
```bash
python manage.py create_test_data
```

## Admin Panel

- URL: http://localhost:8000/admin/
- Username: admin
- Password: admin123

## Quick Test

1. Start server: `daphne -b 127.0.0.1 -p 8000 core.asgi:application`
2. Open browser: http://localhost:8000/login
3. Login as testuser1
4. Open another tab, login as testuser2
5. Send messages and see real-time updates!
