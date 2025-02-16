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
from .serializers import RoomSerializer, MessageSerializer
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




def login_page(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'user dors not exist')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'username or password doest not exist')
    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logout_page(request):
    logout(request)
    return redirect('home')


def register_page(request):
    page = 'register'
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            return redirect('login')
        else:
            messages.error(request, 'an error occured during registration')
    context = {'page': page, 'form': form}

    return render(request, 'base/login_register.html', context)


# def home(request):
#     q = request.GET.get('q') if request.GET.get('q') != None else ''
#     rooms = Room.objects.filter(Q(topic__name__icontains=q) |
#                                 Q(name__icontains=q) |
#                                 Q(description__icontains=q)
#                                 )

#     topics = Topic.objects.all()[0:5]
#     room_count = rooms.count()
#     room_message = Message.objects.filter(
#         Q(room__name__icontains=q)).order_by('-created')[:3]

#     context = {'rooms': rooms, 'topics': topics,
#                'room_count': room_count, 'room_message': room_message}
#     return render(request, 'base/home.html', context)


# @login_required(login_url='login')
# def room(request, pk):
#     room = Room.objects.get(id=pk)
#     comments = room.message_set.all()
#     participants = room.participants.all()

#     if request.method == 'POST':
#         message = Message.objects.create(
#             user=request.user,
#             room=room,
#             body=request.POST.get('body')
#         )
#         room.participants.add(request.user)
#         return redirect('room', pk=room.id)
#     context = {'room': room, 'comments': comments,
#                'participants': participants}

#     return render(request, 'base/room.html', context)


@login_required(login_url='login')
def create_room(request):

    form = RoomForm()
    # topics = Topic.objects.all()

    if request.method == 'POST':
        form = RoomForm(request.POST)
      

        Room.objects.create(
            host=request.user,
            name=request.POST.get('name'),
            description=request.POST.get('description')

        )
       
        return redirect('home')
    context = {'form': form}
    return render(request, 'base/room_form.html', context)


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_message = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms,
               'room_message': room_message, 'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('Access Denied')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')

        return redirect('home')
    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def delete_room(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('Access Denied')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def delete_message(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('Access Denied')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')
def update_user(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    context = {'form': form}

    return render(request, 'base/update_user.html', context)


def topic_page(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__contains=q)
    context = {'topics': topics}

    return render(request, 'base/topics.html', context)


def activity(request):
    room_messages = Message.objects.all().order_by('-created')[:3]
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)


def football(request):
    # Replace with your actual API key


    APIkey = "pC6q3bn1g3Ivi6EG"
    current_date = date.today()
    from_date = current_date.strftime("%Y-%m-%d")
    to_date = from_date
    # url = f"http://api.isportsapi.com/sport/football/schedule/basic?api_key={APIkey}&from={from_date}&to={to_date}"
    # url = f"http://api.isportsapi.com/sport/football/schedule/basic?api_key={APIkey}&leagueId=1639"
    # odds_url = f"http://api.isportsapi.com/sport/football/odds/european/all?api_key={APIkey}&leagueId=1639"
    premier_league_fixtures = {
    "fixtures": [
       {"id": 1, "home": "Manchester United", "away": "Liverpool", "homeodd": 2.10, "awayodd": 1.20, "drawodd": 3.0},
        {"id": 2, "home": "Arsenal", "away": "Chelsea", "homeodd": 2.10, "awayodd": 1.20, "drawodd": 3.0},
        {"id": 3, "home": "Manchester City", "away": "Tottenham", "homeodd": 2.10, "awayodd": 1.20, "drawodd": 3.0},
        {"id": 4, "home": "Everton", "away": "West Ham", "homeodd": 2.30, "awayodd": 1.50, "drawodd": 2.80},
        {"id": 5, "home": "Aston Villa", "away": "Brighton", "homeodd": 2.40, "awayodd": 1.60, "drawodd": 2.90},
        {"id": 6, "home": "Newcastle", "away": "Wolves", "homeodd": 2.20, "awayodd": 1.80, "drawodd": 3.10},
        {"id": 7, "home": "Leicester", "away": "Crystal Palace", "homeodd": 2.00, "awayodd": 1.90, "drawodd": 3.20},
        {"id": 8, "home": "Southampton", "away": "Brentford", "homeodd": 2.50, "awayodd": 1.70, "drawodd": 2.85},
        {"id": 9, "home": "Fulham", "away": "Nottingham Forest", "homeodd": 2.15, "awayodd": 1.95, "drawodd": 3.05},
        {"id": 10, "home": "Leeds", "away": "Bournemouth", "homeodd": 2.35, "awayodd": 1.65, "drawodd": 2.75}
    ]}



    # try:
        # Make the API call
        # response = requests.get(premier_league_fixtures, timeout=30)
        # response2 = requests.get(odds_url, timeout=30)

        # response.raise_for_status()
        # response2.raise_for_status()  # Raise an HTTPError if the status code is 4xx or 5xx
        # Parse the JSON response
        # data = response.json()
        # data2 = response2.json()

        # Pass the data to the template
        # print(data)
    context = {"fixtures": premier_league_fixtures["fixtures"]}
    return render(request, 'base/football.html',context)
    # except requests.exceptions.RequestException as e:
        # Handle exceptions (e.g., timeout, connection error)
        # error_message = f"Error fetching fixtures: {e}"
        # return render(request, 'base/football.html', {'error': error_message})


def basketball(request):
    basketball_fixtures = {
    "fixtures": [
         {"id": 1, "home": "Los Angeles Lakers", "away": "Golden State Warriors", "homeodd": 1.80, "awayodd": 2.00, "drawodd": 3.10},
        {"id": 2, "home": "Brooklyn Nets", "away": "Milwaukee Bucks", "homeodd": 2.10, "awayodd": 1.75, "drawodd": 3.20},
        {"id": 3, "home": "Chicago Bulls", "away": "Miami Heat", "homeodd": 1.90, "awayodd": 1.95, "drawodd": 3.00},
        {"id": 4, "home": "Phoenix Suns", "away": "Denver Nuggets", "homeodd": 1.85, "awayodd": 2.05, "drawodd": 3.25},
        {"id": 5, "home": "Philadelphia 76ers", "away": "Boston Celtics", "homeodd": 2.00, "awayodd": 1.85, "drawodd": 3.15},
        {"id": 6, "home": "New York Knicks", "away": "Toronto Raptors", "homeodd": 1.75, "awayodd": 2.10, "drawodd": 3.30},
        {"id": 7, "home": "Dallas Mavericks", "away": "Memphis Grizzlies", "homeodd": 2.20, "awayodd": 1.70, "drawodd": 3.10},
        {"id": 8, "home": "Cleveland Cavaliers", "away": "Atlanta Hawks", "homeodd": 1.95, "awayodd": 2.00, "drawodd": 3.05},
        {"id": 9, "home": "Utah Jazz", "away": "Portland Trail Blazers", "homeodd": 2.15, "awayodd": 1.85, "drawodd": 3.40},
        {"id": 10, "home": "Sacramento Kings", "away": "San Antonio Spurs", "homeodd": 1.90, "awayodd": 2.10, "drawodd": 3.20}
    ]
}
    context = {"fixtures": basketball_fixtures["fixtures"]}
    return render(request, 'base/football.html',context)
    
def hockey(request):
    hockey_fixtures = {
    "fixtures": [
        {"id": 1, "home": "Toronto Maple Leafs", "away": "Montreal Canadiens", "homeodd": 2.00, "awayodd": 1.90, "drawodd": 3.60},
        {"id": 2, "home": "Edmonton Oilers", "away": "Calgary Flames", "homeodd": 1.85, "awayodd": 2.10, "drawodd": 3.50},
        {"id": 3, "home": "Boston Bruins", "away": "New York Rangers", "homeodd": 1.95, "awayodd": 2.00, "drawodd": 3.45},
        {"id": 4, "home": "Pittsburgh Penguins", "away": "Washington Capitals", "homeodd": 2.10, "awayodd": 1.85, "drawodd": 3.40},
        {"id": 5, "home": "Chicago Blackhawks", "away": "Detroit Red Wings", "homeodd": 2.20, "awayodd": 1.80, "drawodd": 3.35},
        {"id": 6, "home": "Los Angeles Kings", "away": "San Jose Sharks", "homeodd": 2.00, "awayodd": 1.95, "drawodd": 3.55},
        {"id": 7, "home": "Colorado Avalanche", "away": "Vegas Golden Knights", "homeodd": 1.75, "awayodd": 2.25, "drawodd": 3.30},
        {"id": 8, "home": "Tampa Bay Lightning", "away": "Florida Panthers", "homeodd": 2.05, "awayodd": 1.90, "drawodd": 3.45},
        {"id": 9, "home": "St. Louis Blues", "away": "Minnesota Wild", "homeodd": 1.95, "awayodd": 2.05, "drawodd": 3.50},
        {"id": 10, "home": "New Jersey Devils", "away": "Buffalo Sabres", "homeodd": 2.15, "awayodd": 1.85, "drawodd": 3.40}
    ]
}
    context = {"fixtures": hockey_fixtures["fixtures"]}

    return render(request, 'base/hockey.html',context)

def nfl(request):
    nfl_fixtures = {
    "fixtures": [
        {"id": 1, "home": "Kansas City Chiefs", "away": "Buffalo Bills", "homeodd": 1.90, "awayodd": 2.00, "drawodd": 3.50},
        {"id": 2, "home": "Dallas Cowboys", "away": "Philadelphia Eagles", "homeodd": 2.10, "awayodd": 1.85, "drawodd": 3.40},
        {"id": 3, "home": "San Francisco 49ers", "away": "Los Angeles Rams", "homeodd": 1.95, "awayodd": 2.05, "drawodd": 3.60},
        {"id": 4, "home": "Green Bay Packers", "away": "Minnesota Vikings", "homeodd": 2.00, "awayodd": 1.90, "drawodd": 3.45},
        {"id": 5, "home": "Miami Dolphins", "away": "New York Jets", "homeodd": 2.20, "awayodd": 1.80, "drawodd": 3.30},
        {"id": 6, "home": "Baltimore Ravens", "away": "Pittsburgh Steelers", "homeodd": 1.85, "awayodd": 2.15, "drawodd": 3.55},
        {"id": 7, "home": "Seattle Seahawks", "away": "Arizona Cardinals", "homeodd": 1.75, "awayodd": 2.25, "drawodd": 3.25},
        {"id": 8, "home": "Indianapolis Colts", "away": "Tennessee Titans", "homeodd": 2.30, "awayodd": 1.70, "drawodd": 3.20},
        {"id": 9, "home": "New Orleans Saints", "away": "Carolina Panthers", "homeodd": 2.05, "awayodd": 1.95, "drawodd": 3.35},
        {"id": 10, "home": "Denver Broncos", "away": "Las Vegas Raiders", "homeodd": 2.15, "awayodd": 1.85, "drawodd": 3.50}
    ]
}
    context = {"fixtures": nfl_fixtures["fixtures"]}

    return render(request, 'base/nfl.html',context)


def politics(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
                                Q(name__icontains=q) |
                                Q(description__icontains=q)
                                )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_message = Message.objects.filter(
        Q(room__name__icontains=q)).order_by('-created')[:3]

    context = {'rooms': rooms, 'topics': topics,
               'room_count': room_count, 'room_message': room_message}

    return render(request, 'base/politics.html', context)


def entertainment(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
                                Q(name__icontains=q) |
                                Q(description__icontains=q)
                                )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_message = Message.objects.filter(
        Q(room__name__icontains=q)).order_by('-created')[:3]

    context = {'rooms': rooms, 'topics': topics,
               'room_count': room_count, 'room_message': room_message}

    return render(request, 'base/entertainment.html', context)
