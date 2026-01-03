from rest_framework import serializers
from .models import CustomUser, Branch, Shipment, CourierStaff, ShipmentTracking, Payment
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# -------------------- Safe JWT Login Serializer --------------------
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Use email as the login field
    username_field = 'email'

    def validate(self, attrs):
        # attrs has email & password
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this email.")

            if not user.check_password(password):
                raise serializers.ValidationError("Incorrect password.")

            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")

            # Call parent to generate token
            data = super().validate({"email": user.email, "password": password})

            # Optionally include user info in the token response
            data.update({
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            })
            return data

        raise serializers.ValidationError("Must include 'email' and 'password'.")
        

# -------------------- User Serializers --------------------
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


# -------------------- Branch Serializer --------------------
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


# -------------------- Shipment Tracking --------------------
class ShipmentTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentTracking
        fields = ['id', 'status', 'updated_at', 'location']


# -------------------- Shipment Serializer --------------------
class ShipmentSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    courier = serializers.SerializerMethodField()
    tracking_updates = ShipmentTrackingSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number', 'sender_name', 'sender_address',
            'receiver_name', 'receiver_address', 'weight', 'package_type',
            'status', 'pickup_date', 'delivery_date', 'created_by',
            'branch', 'courier', 'tracking_updates'
        ]

    def get_courier(self, obj):
        if obj.courier:
            return {
                "id": obj.courier.id,
                "user": {
                    "id": obj.courier.user.id,
                    "username": obj.courier.user.username,
                    "email": obj.courier.user.email
                },
                "branch": {
                    "id": obj.courier.branch.id,
                    "name": obj.courier.branch.name
                },
                "is_available": obj.courier.is_available
            }
        return None


# -------------------- Courier Staff Serializer --------------------
class CourierStaffSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    branch = BranchSerializer(read_only=True)
    assigned_shipments = ShipmentSerializer(many=True, read_only=True)

    class Meta:
        model = CourierStaff
        fields = ['id', 'user', 'branch', 'is_available', 'assigned_shipments']


# -------------------- Payment Serializer --------------------
class PaymentSerializer(serializers.ModelSerializer):
    shipment = ShipmentSerializer(read_only=True)
    shipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Shipment.objects.all(), write_only=True, source='shipment'
    )

    class Meta:
        model = Payment
        fields = ['id', 'shipment', 'shipment_id', 'payment_type', 'amount', 'status', 'payment_date']
