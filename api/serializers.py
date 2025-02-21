from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Room,Message,Ticket,TicketGame




class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    comfirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'comfirm_password')

    def validate(self, attrs):
        if attrs['password'] != attrs['comfirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)        


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class RoomSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)  # Serialize host details
    participants = UserSerializer(many=True, read_only=True)  # Serialize participants
    topic = serializers.StringRelatedField()  # Show topic name instead of ID

    class Meta:
        model = Room
        fields = '__all__'  # Include all fields in the response

class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Serialize user details
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all())  # Send room ID

    class Meta:
        model = Message
        fields = '__all__'


class UserFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']  # Include only relevant fields


class RoomFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'  # Include all fields
        extra_kwargs = {
            'host': {'read_only': True},  # Prevent modification of host
            'participants': {'read_only': True},  # Prevent modification of participants
        }



class UserProfileSerializer(serializers.ModelSerializer):

    rooms = RoomSerializer(many=True, read_only=True)
    room_message = MessageSerializer(many=True, read_only=True)
    # topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'rooms', 'room_message', 'topics']        




class TicketGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketGame
        fields = ['game', 'selected_team', 'odds']

class TicketSerializer(serializers.ModelSerializer):
    games = TicketGameSerializer(many=True)

    class Meta:
        model = Ticket
        fields = ['id', 'user', 'games', 'total_odds', 'is_active', 'created_at']

    def create(self, validated_data):
        games_data = validated_data.pop('games')
        ticket = Ticket.objects.create(**validated_data)
        for game_data in games_data:
            TicketGame.objects.create(ticket=ticket, **game_data)
        return ticket