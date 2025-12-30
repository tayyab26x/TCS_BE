# courier/helpers.py

from .models import Shipment, ShipmentTracking, CourierStaff
from django.utils import timezone

def assign_shipment_to_courier(shipment):
    """
    Assign a shipment to an available courier in the same branch.
    If no staff is available, the shipment stays in warehouse.
    Also creates a ShipmentTracking entry.
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
    else:
        shipment.status = 'in_warehouse'
        shipment.save()
        
        ShipmentTracking.objects.create(
            shipment=shipment,
            status='in_warehouse',
            location=shipment.branch.name
        )


def update_shipment_status(shipment, new_status, location=None):
    """
    Update shipment status and automatically create a ShipmentTracking entry.
    """
    shipment.status = new_status
    shipment.save()
    
    ShipmentTracking.objects.create(
        shipment=shipment,
        status=new_status,
        location=location if location else shipment.branch.name
    )


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
