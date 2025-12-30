from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('super_manager', 'Super Manager / HR'),
        ('manager', 'Manager'),
        ('staff', 'Courier Staff'),
        ('customer', 'Customer'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer',
        verbose_name='User Role'
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    
class Branch(models.Model):
    name = models.CharField(max_length=100)
    location = models.TextField()
    manager = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'role': 'manager'},
        related_name='managed_branches'
    )
    contact_number = models.CharField(max_length=15)
    opening_hours = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

    
class CourierStaff(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'staff'}
    )
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='staff_members')
    assigned_shipments = models.ManyToManyField('Shipment', blank=True, related_name='assigned_staff')
    is_available = models.BooleanField(default=True)  # True = on duty

    def __str__(self):
        return self.user.username


class Shipment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),           # Created, waiting for pickup
        ('in_warehouse', 'In Warehouse'), # At branch warehouse
        ('out_for_delivery', 'Out for Delivery'), # Picked by courier
        ('delivered', 'Delivered'),       # Successfully delivered
        ('cancelled', 'Cancelled'),       # Cancelled
    )

    tracking_number = models.CharField(max_length=20, unique=True)
    sender_name = models.CharField(max_length=100)
    sender_address = models.TextField()
    receiver_name = models.CharField(max_length=100)
    receiver_address = models.TextField()
    weight = models.DecimalField(max_digits=6, decimal_places=2)  # kg
    package_type = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pickup_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='shipments')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='shipments')
    courier = models.ForeignKey(CourierStaff, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipments')

    def __str__(self):
        return f"{self.tracking_number} - {self.status}"


class ShipmentTracking(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_updates')
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    updated_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=100, blank=True)  # optional, e.g., warehouse name or city

    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.status} at {self.updated_at}"



class Payment(models.Model):
    PAYMENT_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('online', 'Online'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    )

    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name='payment')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.status == 'paid' and self.payment_date is None:
            self.payment_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.status}"
