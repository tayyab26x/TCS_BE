from rest_framework import serializers
from .models import CustomUser, Branch, Shipment, CourierStaff, ShipmentTracking, Payment

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role']

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'location', 'manager', 'contact_number', 'opening_hours']

class CourierStaffSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    class Meta:
        model = CourierStaff
        fields = ['id', 'user', 'branch', 'is_available', 'assigned_shipments']

class ShipmentTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentTracking
        fields = ['id', 'status', 'updated_at', 'location']

class ShipmentSerializer(serializers.ModelSerializer):
    tracking_updates = ShipmentTrackingSerializer(many=True, read_only=True)
    class Meta:
        model = Shipment
        fields = [
            'id', 'tracking_number', 'sender_name', 'sender_address', 
            'receiver_name', 'receiver_address', 'weight', 'package_type',
            'status', 'pickup_date', 'delivery_date', 'created_by', 
            'branch', 'courier', 'tracking_updates'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    shipment = ShipmentSerializer(read_only=True)
    class Meta:
        model = Payment
        fields = ['id', 'shipment', 'payment_type', 'amount', 'status', 'payment_date']
