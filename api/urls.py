from django.urls import path
from . import views


urlpatterns = [

    path('', views.home, name='home'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('sign_up/', views.register_page, name='register'),
    path('room/<str:pk>/', views.room, name='room'),
    path('create_room/', views.create_room, name='create-room'),
    path('user_profile/<str:pk>/', views.user_profile, name='user-profile'),
    path('edit_room/<str:pk>/', views.update_room, name='edit-room'),
    path('delete_room/<str:pk>/', views.delete_room, name='delete-room'),
    path('delete_message/<str:pk>/', views.delete_message, name='delete-message'),
    path('update_user/', views.update_user, name='update-user'),
    path('topics/', views.topic_page, name='topics'),
    path('activity/', views.activity, name='activity'),
    path('football/', views.football, name='football'),
    path('politics/', views.politics, name='politics'),
    path('entertainment/', views.entertainment, name='entertainment'),
    path('basketball/',views.basketball,name='basketball'),
    path('hockey/',views.hockey,name='hockey'),
    path('nfl/',views.nfl,name='nfl'),


]
