from rest_framework import serializers
from user.models import CustomUser
from . models import EmailChangeOTP,Address, GiftCard, SavedUPI, SavedCard, Order, OrderItem
import secrets
from django.core.mail import  send_mail
from django.conf import settings
# from django.contrib.auth.password_validation import validate_password
# from django.core.exceptions import ValidationError as DjangoValidationError

class EmailChangeRequestSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

    def validate_new_email(self,value):
        user = self.context['request'].user
        if CustomUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError('This email is already in use')
        if value == user.email:
            raise serializers.ValidationError('This is your current one ')
        return value

    def save(self):
        user = self.context['request'].user
        new_email = self.validated_data['new_email']
        otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))

        otp_obj = EmailChangeOTP.objects.create(
            user =user,
            otp=otp_code,
            new_email=new_email
        )

        send_mail(
            subject="Verify yours new email",
            message=f'Yours otp for email change is {otp_code} hurry up it can expiry after 5 minutes ',
            from_email = settings.DEFAULT_FROM_EMAIL,
            recipient_list=[new_email],
        )
        return otp_obj


class EmailChangeVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        user = self.context['request'].user
        try:
            otp_obj = EmailChangeOTP.objects.filter(
                user = user , otp=data['otp'], is_verified=False
            ).latest('created_at')
        except EmailChangeOTP.DoesNotExist:
            raise serializers.ValidationError({"otp":"invalid OTP"})

        if otp_obj.is_expired():
            raise serializers.ValidationError({"opt":"otp has expired | please request once again"})

        data['otp_obj'] = otp_obj
        return data

    def save(self):
        otp_obj = self.validated_data['otp_obj']
        user = otp_obj.user
        user.email = otp_obj.new_email
        user.save()

        otp_obj.is_verified = True
        otp_obj.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'read_only': True},   # email is changed only via OTP flow, not here
            'username': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_username(self, value):
        user = self.context['request'].user
        if CustomUser.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value


class AddressSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    address_line1 = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)

    class Meta:
        model = Address
        exclude = ("user",)
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        coordinates = ("latitude", "longitude")
        has_coordinates = all(attrs.get(field) is not None for field in coordinates)
        has_manual_address = all(attrs.get(field) for field in (
            "recipient_name", "phone_number", "address_line1", "city", "state", "postal_code"
        ))
        if not has_coordinates and not has_manual_address:
            raise serializers.ValidationError(
                "Provide latitude and longitude, or complete the manual address fields."
            )
        if attrs.get("latitude") is not None and not -90 <= attrs["latitude"] <= 90:
            raise serializers.ValidationError({"latitude": "Latitude must be between -90 and 90."})
        if attrs.get("longitude") is not None and not -180 <= attrs["longitude"] <= 180:
            raise serializers.ValidationError({"longitude": "Longitude must be between -180 and 180."})
        return attrs


class GiftCardSerializer(serializers.ModelSerializer):
    card_number = serializers.CharField(write_only=True, required=False, min_length=4)
    gift_card_token = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = GiftCard
        exclude = ("user",)
        read_only_fields = ("last_four", "created_at")

    def create(self, validated_data):
        card_number = validated_data.pop("card_number", "")
        validated_data["last_four"] = card_number[-4:] if card_number else ""
        return super().create(validated_data)


class SavedUPISerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedUPI
        exclude = ("user",)
        read_only_fields = ("created_at",)


class SavedCardSerializer(serializers.ModelSerializer):
    card_number = serializers.CharField(write_only=True, required=False, min_length=4)
    payment_token = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = SavedCard
        exclude = ("user",)
        read_only_fields = ("last_four", "created_at")

    def create(self, validated_data):
        card_number = validated_data.pop("card_number", "")
        if not card_number and not validated_data.get("last_four"):
            raise serializers.ValidationError({"card_number": "This field is required."})
        validated_data["last_four"] = card_number[-4:] if card_number else validated_data["last_four"]
        validated_data.pop("last_four", None)
        return super().create(validated_data)

    def validate_expiry_month(self, value):
        if not 1 <= value <= 12:
            raise serializers.ValidationError("Expiry month must be between 1 and 12.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        exclude = ("order",)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        exclude = ("user",)
        read_only_fields = ("order_number", "placed_at", "updated_at")
