from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import HomeView,ProtectedView,LogoutView,DeleteRoomAPIView, RoomDetailView, CreateRoomView,LoginView,RegisterView





urlpatterns = [

    path('', HomeView.as_view() , name='home'),
    path("register/", RegisterView.as_view(), name="register"),
    path('login/', LoginView.as_view(), name='login'),
    path('protected-endpoint/', ProtectedView.as_view(), name='protected-endpoint'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('createroom/', CreateRoomView.as_view(), name='create_room'),
    path('room/<str:pk>/', RoomDetailView.as_view(), name='room_detail'),
    path('room/<str:pk>/delete/', DeleteRoomAPIView.as_view(), name='delete-room'),

    path('logout/',LogoutView.as_view(),name='logout')


    # path('logout/', views.logout_page, name='logout'),
    # path('sign_up/', views.register_page, name='register'),
    # path('user_profile/<str:pk>/', views.user_profile, name='user-profile'),
    # path('edit_room/<str:pk>/', views.update_room, name='edit-room'),
    # path('delete_room/<str:pk>/', views.delete_room, name='delete-room'),
    # path('delete_message/<str:pk>/', views.delete_message, name='delete-message'),
    # path('update_user/', views.update_user, name='update-user'),
    # path('topics/', views.topic_page, name='topics'),
    # path('activity/', views.activity, name='activity'),
    # path('football/', views.football, name='football'),
    # path('politics/', views.politics, name='politics'),
    # path('entertainment/', views.entertainment, name='entertainment'),
    # path('basketball/',views.basketball,name='basketball'),
    # path('hockey/',views.hockey,name='hockey'),
    # path('nfl/',views.nfl,name='nfl'),

]
