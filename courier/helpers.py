# courier/helpers.py

from datetime import timedelta
from django.utils import timezone
from .models import Shipment, ShipmentTracking, CourierStaff, Notification

# ---------------------------
# Assign a shipment to available courier
# ---------------------------
def assign_shipment_to_courier(shipment):
    """
    Assign a shipment to an available courier in the same branch.
    If no staff is available, the shipment stays in warehouse.
    Also creates a ShipmentTracking entry and calculates ETA.
    """
    available_staff = shipment.branch.staff_members.filter(is_available=True)
    
    if available_staff.exists():
        courier = available_staff.first()  # pick the first available
        shipment.courier = courier
        shipment.status = 'out_for_delivery'
        shipment.save()
        
        courier.assigned_shipments.add(shipment)
        
        # Add tracking update
        ShipmentTracking.objects.create(
            shipment=shipment,
            status='out_for_delivery',
            location=shipment.branch.name
        )
        
        # Calculate estimated delivery
        calculate_eta(shipment)
        
        # Notify customer
        notify_customer(
            shipment,
            f"Your shipment {shipment.tracking_number} has been assigned to courier {courier.user.username} and is out for delivery."
        )
        
    else:
        shipment.status = 'in_warehouse'
        shipment.save()
        
        ShipmentTracking.objects.create(
            shipment=shipment,
            status='in_warehouse',
            location=shipment.branch.name
        )
        
        notify_customer(
            shipment,
            f"Your shipment {shipment.tracking_number} is in warehouse. Waiting for available courier."
        )

# ---------------------------
# Update shipment status with tracking
# ---------------------------
def update_shipment_status(shipment, new_status, location=None):
    """
    Update shipment status and automatically create a ShipmentTracking entry.
    Also notifies the customer.
    """
    shipment.status = new_status
    shipment.save()
    
    ShipmentTracking.objects.create(
        shipment=shipment,
        status=new_status,
        location=location if location else (shipment.branch.name if shipment.branch else "N/A")
    )
    
    notify_customer(
        shipment,
        f"Your shipment {shipment.tracking_number} status has been updated to {new_status}."
    )

# ---------------------------
# Calculate estimated delivery based on service type
# ---------------------------
def calculate_eta(shipment):
    """
    Estimate delivery date based on service_type.
    """
    now = timezone.now()
    if shipment.service_type == 'same_day':
        shipment.estimated_delivery = now + timedelta(hours=6)
    elif shipment.service_type == 'overnight':
        shipment.estimated_delivery = now + timedelta(days=1)
    elif shipment.service_type == 'economy':
        shipment.estimated_delivery = now + timedelta(days=3)
    elif shipment.service_type == 'international':
        shipment.estimated_delivery = now + timedelta(days=7)
    shipment.save()
    return shipment.estimated_delivery

# ---------------------------
# Notifications
# ---------------------------
def notify_customer(shipment, message, notification_type='email'):
    """
    Send a notification to the customer and log it.
    """
    Notification.objects.create(
        user=shipment.created_by,
        shipment=shipment,
        message=message,
        notification_type=notification_type
    )

# ---------------------------
# Courier duty management
# ---------------------------
def mark_courier_on_duty(courier_staff):
    """
    Mark a courier as available/on-duty.
    """
    courier_staff.is_available = True
    courier_staff.save()

def mark_courier_off_duty(courier_staff):
    """
    Mark a courier as unavailable/off-duty.
    Reassign their pending shipments automatically if needed.
    """
    courier_staff.is_available = False
    courier_staff.save()
    
    # Reassign all pending shipments assigned to this courier
    pending_shipments = courier_staff.assigned_shipments.filter(
        status__in=['pending', 'in_warehouse', 'out_for_delivery']
    )
    
    for shipment in pending_shipments:
        # Remove from current courier
        courier_staff.assigned_shipments.remove(shipment)
        shipment.courier = None
        shipment.status = 'in_warehouse'
        shipment.save()
        
        # Reassign automatically
        assign_shipment_to_courier(shipment)

# ---------------------------
# Query helpers
# ---------------------------
def get_customer_shipments(customer):
    """
    Return all shipments created by a customer.
    """
    return Shipment.objects.filter(created_by=customer).order_by('-pickup_date')

def get_branch_shipments(branch):
    """
    Return all shipments for a branch.
    """
    return Shipment.objects.filter(branch=branch).order_by('-pickup_date')

def get_courier_shipments(courier_staff):
    """
    Return all shipments assigned to a courier staff.
    """
    return courier_staff.assigned_shipments.all().order_by('-pickup_date')
