from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import requests
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token



from . serializers import (
    RegisterSerializer,
    LoginSerializer,
    GoogleLoginSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# pyrefly: ignore [missing-import]
from .models import OTPVerification
import random


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        if user is None:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        # Add staff permissions to the JWT claims.
        refresh["is_staff"] = user.is_staff
        refresh["is_superuser"] = user.is_superuser

        return Response({
            "message": "Login successful",
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class GoogleLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = GoogleLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            profile = self._get_google_profile(serializer.validated_data)
        except (GoogleAuthError, ValueError, requests.RequestException):
            return Response(
                {"error": "Invalid Google token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user = self._get_or_create_user(profile)
        except IntegrityError:
            user = User.objects.get(email__iexact=profile["email"])

        refresh = RefreshToken.for_user(user)
        refresh["is_staff"] = user.is_staff
        refresh["is_superuser"] = user.is_superuser

        return Response(
            {
                "message": "Google login successful",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _client_id():
        client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
        if not client_id:
            raise ValueError("Google OAuth client ID is not configured.")
        return client_id

    @classmethod
    def _get_google_profile(cls, credentials):
        if "id_token" in credentials:
            claims = google_id_token.verify_oauth2_token(
                credentials["id_token"],
                GoogleRequest(),
                audience=cls._client_id(),
            )
            if not claims.get("email") or claims.get("email_verified") is not True:
                raise ValueError("Google account email is not verified.")
            return claims

        access_token = credentials["access_token"]
        token_info = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"access_token": access_token},
            timeout=5,
        )
        token_info.raise_for_status()
        if token_info.json().get("aud") != cls._client_id():
            raise ValueError("Google access token audience is invalid.")

        profile_response = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )
        profile_response.raise_for_status()
        profile = profile_response.json()
        if not profile.get("email") or profile.get("email_verified") is not True:
            raise ValueError("Google account email is not verified.")
        return profile

    @staticmethod
    def _get_or_create_user(profile):
        email = profile["email"].lower()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            return user

        username = (profile.get("preferred_username") or email.split("@", 1)[0])[:100]
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                username=username,
                first_name=profile.get("given_name", "")[:100],
                last_name=profile.get("family_name", "")[:100],
                password=None,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
            return user


class SendOTPView(generics.GenericAPIView):
    serializer_class = SendOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.validated_data['email'])

        otp_code = str(random.randint(100000, 999999))
        OTPVerification.objects.create(user=user, otp=otp_code)

        from django.core.mail import send_mail
        send_mail(
            subject="Your OTP Verification Code",
            message=f"Your OTP is: {otp_code}. It will expire in 5 minutes.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']

        try:
            otp = OTPVerification.objects.filter(
                user__email=email, otp=otp_code, is_verified=False
            ).latest('created_at')
        except OTPVerification.DoesNotExist:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)

        otp.is_verified = True
        otp.save()
        return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
