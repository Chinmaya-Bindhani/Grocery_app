"""
PROJECT LEVEL URLS

"""
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("user.urls")),
    path("api/user-profile/", include("User_Profile.urls")),
]
