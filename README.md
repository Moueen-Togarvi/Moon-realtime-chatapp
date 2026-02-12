# Moon Realtime Chatapp

A real-time chat application built with Django, Channels, and Tailwind CSS.

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r core/requirements.txt
   ```

2. **Database Migrations**
   ```bash
   cd core
   python manage.py migrate
   ```

3. **Run Server with Daphne**
   ```bash
   daphne -p 8000 core.asgi:application
   ```

Refer to the [detailed README](core/README.md) in the `core` directory for more information.