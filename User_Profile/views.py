from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import  Address, GiftCard, SavedUPI, SavedCard, Order
from .geolocation import IPGeolocation
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import  generics
from .serializers import (
    ProfileSerializer,
    EmailChangeRequestSerializer,
    EmailChangeVerifySerializer,
    AddressSerializer,
    GiftCardSerializer,
    SavedUPISerializer,
    SavedCardSerializer,
    OrderSerializer,
)


class ProfileView(APIView):
    """
    GET   -> returns the logged-in user's profile info
    PATCH -> updates First_name, Last_name, username (not email)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmailChangeRequestView(APIView):
    """
    POST -> accepts new_email, generates OTP, emails it to new_email
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailChangeRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "OTP sent to new email."},
            status=status.HTTP_200_OK
        )


class EmailChangeVerifyView(APIView):
    """
    POST -> accepts otp, verifies it, updates user's email if valid
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailChangeVerifySerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"detail": "Email updated successfully.", "email": user.email},
            status=status.HTTP_200_OK
        )

class UserOwnedCollectionView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressView(UserOwnedCollectionView):
    model = Address
    serializer_class = AddressSerializer
    throttle_scope = "profile"

    def get(self, request, *args, **kwargs):
        location = IPGeolocation().locate(request.META.get("REMOTE_ADDR"))
        return Response({
            "location": location,
            "location_available": location is not None,
            "addresses": AddressSerializer(self.get_queryset(), many=True).data,
            "manual_address_fields": [
                "recipient_name", "phone_number", "address_line1",
                "address_line2", "city", "state", "postal_code",
            ],
        })

    def create(self, request, *args, **kwargs):
        manual_fields = (
            "recipient_name", "phone_number", "address_line1",
            "city", "state", "postal_code",
        )
        has_manual_address = all(request.data.get(field) for field in manual_fields)
        has_gps = (
            request.data.get("latitude") is not None
            and request.data.get("longitude") is not None
        )
        if not has_manual_address:
            location = None
            if not has_gps:
                location = IPGeolocation().locate(request.META.get("REMOTE_ADDR"))
            return Response({
                "requires_manual_address": True,
                "message": (
                    "Location was detected. Complete the remaining address fields."
                    if location else
                    "Automatic location lookup failed. Complete the address form."
                ),
                "location": location or {
                    "latitude": request.data.get("latitude"),
                    "longitude": request.data.get("longitude"),
                },
                "fields": [
                    "recipient_name", "phone_number", "address_line1",
                    "address_line2", "city", "state", "postal_code",
                ],
            }, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)


class GiftCardView(UserOwnedCollectionView):
    model = GiftCard
    serializer_class = GiftCardSerializer
    throttle_scope = "payment"


class SavedUPIView(UserOwnedCollectionView):
    model = SavedUPI
    serializer_class = SavedUPISerializer
    throttle_scope = "payment"


class SavedCardView(UserOwnedCollectionView):
    model = SavedCard
    serializer_class = SavedCardSerializer
    throttle_scope = "payment"


class OrdersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "orders"
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items")

    def list(self, request, *args, **kwargs):
        orders = list(self.get_queryset())
        current_statuses = {"pending", "confirmed", "processing", "shipped", "out_for_delivery"}
        current = [order for order in orders if order.status in current_statuses]
        previous = [order for order in orders if order.status not in current_statuses]
        return Response({
            "current_orders": self.get_serializer(current, many=True).data,
            "previous_orders": self.get_serializer(previous, many=True).data,
            "total_orders": len(orders),
        })
