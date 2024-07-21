from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from ..models import CustomUser


class UserSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=50)
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'refreshToken', 'password')
        extra_kwargs = {"password":{"write_only":True}} 

    def validate(self, attrs):
        print(attrs)
        return super().validate(attrs)
    def create(self, validated_data):
        if not CustomUser.objects.filter(email=validated_data['email']).exists():
            user = CustomUser.objects.create_user(**validated_data)
            user.set_password(validated_data['password'])
            user.save()
            return user
        else:
            return False