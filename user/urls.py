from django.urls import  path
from . views import (
    RegisterView,
    LoginView,
    GoogleLoginView,
    SendOTPView,
    VerifyOTPView,
    ChangePasswordView,
)

urlpatterns=[
    path('register/',RegisterView.as_view(),name='register'),
    path('login/',LoginView.as_view(),name='Login'),
    path('google/', GoogleLoginView.as_view(), name='google-login'),# for google authentications 
    path('send-otp/',SendOTPView.as_view(),name='send-otp'),
    path('verify-otp/',VerifyOTPView.as_view(),name='verify-otp'),
    path('change-password/',ChangePasswordView.as_view(),name='change-password_view'),
]

