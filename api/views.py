from django.shortcuts import render, redirect
from .models import Room, Topic, Message
from .forms import RoomForm, UserForm
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required  
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from datetime import date
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ModelSerializer
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import RoomSerializer, MessageSerializer,UserProfileSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError



class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully.",
                "user": {
                    "username": user.username,
                    "email": user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    "message": "Login successful.",
                    "user": {
                        "username": user.username,
                        "email": user.email,
                    },
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    }
                }, status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LogoutView(APIView):
    def post(self, request):
        try:
            # Get the refresh token from the request data
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
        except TokenError as e:
            # Handle invalid or expired tokens
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Handle other exceptions
            return Response({"error": "An error occurred during logout."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access

    def get(self, request):
        return Response({
            "message": "This is protected data.",
            "user": {
                "username": request.user.username,
                "email": request.user.email,
            }
        }, status=status.HTTP_200_OK)


class CreateRoomView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def post(self, request):
        # Pass request data to the serializer
        serializer = RoomSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Save the room with the current user as the host
            room = serializer.save(host=request.user)
            return Response({
                'status': 'success',
                'message': 'Room created successfully!',
                'room': {
                    'id': room.id,
                    'name': room.name,
                    'description': room.description,
                    'host': room.host.username,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': 'error',
            'message': 'Invalid data.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class RoomDetailView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def get(self, request, pk):
        try:
            room = Room.objects.get(id=pk)
            serializer = RoomSerializer(room)

            messages = room.message_set.all()  # or use the related_name if specified in the model

            message_serializer = MessageSerializer(messages, many=True)

            response_data = serializer.data
            response_data['messages'] = message_serializer.data

            return Response(response_data, status=status.HTTP_200_OK)

            # return Response(serializer.data, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Room not found.'
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        try:
            room = Room.objects.get(id=pk)
            body = request.data.get('body')

            if not body:
                return Response({
                    'status': 'error',
                    'message': 'Message body is required.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create the message
            message = Message.objects.create(
                user=request.user,
                room=room,
                body=body
            )
            room.participants.add(request.user)

            return Response({
                'status': 'success',
                'message': 'Message created successfully!',
                'data': MessageSerializer(message).data
            }, status=status.HTTP_201_CREATED)
        except Room.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Room not found.'
            }, status=status.HTTP_404_NOT_FOUND)




class HomeView(APIView):
    def get(self, request):
        q = request.GET.get('q', '')
        
        # Filter rooms based on the search query
        rooms = Room.objects.filter(
            Q(topic__name__icontains=q) |
            Q(name__icontains=q) |
            Q(description__icontains=q)
        )
        
        # Get the first 5 topics
        topics = Topic.objects.all()[:5]
        
        # Count the number of rooms
        room_count = rooms.count()
        
        # Get the latest 3 messages related to the search query
        room_message = Message.objects.filter(
            Q(room__name__icontains=q)
        ).order_by('-created')[:3]
        
        # Serialize the data
        room_serializer = RoomSerializer(rooms, many=True)
        # topic_serializer = TopicSerializer(topics, many=True)
        message_serializer = MessageSerializer(room_message, many=True)
        
        # Prepare the response data
        response_data = {
            'rooms': room_serializer.data,
            # 'topics': topic_serializer.data,
            'room_count': room_count,
            'room_message': message_serializer.data
        }
        
        # Return the JSON response
        return Response(response_data, status=status.HTTP_200_OK)




class DeleteRoomAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def delete(self, request, pk, format=None):
        try:
            room = Room.objects.get(id=pk)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the requesting user is the host of the room
        if request.user != room.host:
            return Response({"error": "Access Denied"}, status=status.HTTP_403_FORBIDDEN)

        # Delete the room
        room.delete()
        return Response({"message": "Room deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only logged-in users can access this

    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)  # Fetch user or return 404
        rooms = Room.objects.filter(host=user)  # Get rooms created by the user
        room_messages = Message.objects.filter(user=user)  # Get messages sent by the user
        topics = Topic.objects.all()  # Fetch all topics

        # Serialize data
        user_data = UserSerializer(user).data
        rooms_data = RoomSerializer(rooms, many=True).data
        messages_data = MessageSerializer(room_messages, many=True).data
        topics_data = TopicSerializer(topics, many=True).data

        return Response({
            "user": user_data,
            "rooms": rooms_data,
            "room_messages": messages_data,
            "topics": topics_data,
        })


