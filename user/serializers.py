from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
User = get_user_model()



from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser

        return token

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    username = serializers.CharField(max_length=100)
    first_name= serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_email(self,value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("email is already associated with us ")
        return  value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("password and confirm password should be same ")
        return data

    def create(self, validated_data):
        user = User.objects.create(
            email = validated_data['email'],
            username = validated_data['username'],
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            password = validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(
        required=False, allow_blank=False, max_length=4096, write_only=True
    )
    access_token = serializers.CharField(
        required=False, allow_blank=False, max_length=4096, write_only=True
    )

    def validate(self, data):
        if bool(data.get("id_token")) == bool(data.get("access_token")):
            raise serializers.ValidationError(
                "Provide exactly one of id_token or access_token."
            )
        return data


class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})

        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as old password."})

        user = self.context['request'].user
        try:
            validate_password(data['new_password'], user)
        except DjangoValidationError as err:
            raise serializers.ValidationError({"new_password": list(err.messages)})

        return data
