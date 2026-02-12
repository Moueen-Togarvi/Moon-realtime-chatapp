from django.urls import path
from . import views

urlpatterns = [
    path('', views.public_home, name='public_home'),
    path('home/', views.public_home, name='home'),
    path('ai/', views.public_ai, name='public_ai'),
    path('ai/reply/', views.ai_reply, name='ai_reply'),
    path('features/', views.public_features, name='public_features'),
    path('about/', views.public_about, name='public_about'),
    path('contact/', views.public_contact, name='public_contact'),
    path('tools/', views.public_tools, name='public_tools'),
    path('integrations/', views.public_integrations, name='public_integrations'),
    path('use-cases/', views.public_use_cases, name='public_use_cases'),

    # Auth
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),

    # Chat
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<uuid:room_id>/', views.chat_room, name='chat_room'),
    path('chat/create/<uuid:user_id>/', views.create_chat, name='create_chat'),
    path('chat/create-group/', views.create_group_chat, name='create_group_chat'),
    path('search/', views.search_users, name='search_users'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),

    path('upload-media/', views.upload_media, name='upload_media'),

    

]
