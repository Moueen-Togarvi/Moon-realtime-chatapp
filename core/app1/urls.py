from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('chats/', views.chat_list, name='chat_list'),
    path('chat/<uuid:room_id>/', views.chat_room, name='chat_room'),
    path('create-chat/<uuid:user_id>/', views.create_chat, name='create_chat'),
    path('create-group/', views.create_group_chat, name='create_group_chat'),
    path('search-users/', views.search_users, name='search_users'),
    path('notifications/', views.notifications, name='notifications'),
    path('upload-media/', views.upload_media, name='upload_media'),
    path('websocket-test/', views.websocket_test, name='websocket_test'),
]
