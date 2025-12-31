from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# ---------------------------
# Custom User
# ---------------------------
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

# ---------------------------
# Branch
# ---------------------------
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

# ---------------------------
# Courier Staff
# ---------------------------
class CourierStaff(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'staff'}
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        related_name='staff_members'
    )
    assigned_shipments = models.ManyToManyField(
        'Shipment',
        blank=True,
        related_name='assigned_staff'
    )
    is_available = models.BooleanField(default=True)  # True = on duty

    def __str__(self):
        return self.user.username

# ---------------------------
# Shipment
# ---------------------------
class Shipment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),           
        ('in_warehouse', 'In Warehouse'),
        ('out_for_delivery', 'Out for Delivery'), 
        ('delivered', 'Delivered'),       
        ('cancelled', 'Cancelled'),       
    )

    SERVICE_CHOICES = (
        ('same_day', 'Same Day'),
        ('overnight', 'Overnight'),
        ('economy', 'Economy'),
        ('international', 'International'),
    )

    tracking_number = models.CharField(max_length=20, unique=True)
    sender_name = models.CharField(max_length=100)
    sender_address = models.TextField()
    receiver_name = models.CharField(max_length=100)
    receiver_address = models.TextField()
    weight = models.DecimalField(max_digits=6, decimal_places=2)  # kg
    package_type = models.CharField(max_length=50, blank=True)
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, default='economy')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pickup_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shipments'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shipments'
    )
    courier = models.ForeignKey(
        CourierStaff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipments'
    )
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tracking_number} - {self.status}"

# ---------------------------
# Shipment Tracking Updates
# ---------------------------
class ShipmentTracking(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='tracking_updates'
    )
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    updated_at = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.status} at {self.updated_at}"

# ---------------------------
# Payment
# ---------------------------
class Payment(models.Model):
    PAYMENT_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('online', 'Online'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    )

    shipment = models.OneToOneField(
        Shipment,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    payment_type = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.status == 'paid' and self.payment_date is None:
            self.payment_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.status}"

# ---------------------------
# Optional: Rate Model (Pricing Engine)
# ---------------------------
class Rate(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='rates'
    )
    service_type = models.CharField(max_length=20, choices=Shipment.SERVICE_CHOICES)
    weight_from = models.DecimalField(max_digits=6, decimal_places=2)
    weight_to = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.branch.name} - {self.service_type} ({self.weight_from}-{self.weight_to}kg)"

# ---------------------------
# Optional: Notification Model
# ---------------------------
class Notification(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=20, choices=(('sms','SMS'),('email','Email')))

    def __str__(self):
        return f"{self.user.username} - {self.notification_type} at {self.sent_at}"
