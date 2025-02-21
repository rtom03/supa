from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import HomeView,ProtectedView,LogoutView,DeleteRoomAPIView, RoomDetailView, CreateRoomView,LoginView,RegisterView,UserProfileView





urlpatterns = [

    path('', HomeView.as_view() , name='home'),
    path("register/", RegisterView.as_view(), name="register"),
    path('login/', LoginView.as_view(), name='login'),
    path('protected-endpoint/', ProtectedView.as_view(), name='protected-endpoint'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('createroom/', CreateRoomView.as_view(), name='create_room'),
    path('room/<str:pk>/', RoomDetailView.as_view(), name='room_detail'),
    path('room/delete/<str:pk>/', DeleteRoomAPIView.as_view(), name='delete-room'),
    path('user/<str:pk>/', UserProfileView.as_view(), name='user-profile-api'),




    # path('logout/',LogoutView.as_view(),name='logout')



]
