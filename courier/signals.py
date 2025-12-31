# courier/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Shipment, ShipmentTracking
from .helpers import assign_shipment_to_courier, calculate_eta, notify_customer

# ---------------------------
# Create initial tracking & assign courier
# ---------------------------
@receiver(post_save, sender=Shipment)
def shipment_post_save(sender, instance, created, **kwargs):
    """
    Automatically handle shipment creation:
    - Create initial tracking entry
    - Assign courier if available
    - Calculate ETA
    - Notify customer
    """
    if created:
        # Create initial tracking
        ShipmentTracking.objects.create(
            shipment=instance,
            status=instance.status,
            location=instance.branch.name if instance.branch else "N/A"
        )
        
        # Assign courier automatically
        assign_shipment_to_courier(instance)
        
        # Calculate ETA
        calculate_eta(instance)
        
        # Notify customer
        notify_customer(
            instance,
            f"Your shipment {instance.tracking_number} has been created and is currently {instance.status}."
        )


# ---------------------------
# Create tracking update on status change
# ---------------------------
@receiver(pre_save, sender=Shipment)
def shipment_status_change(sender, instance, **kwargs):
    """
    Automatically create a ShipmentTracking entry whenever the shipment status changes.
    """
    if not instance.pk:
        # New shipment, skip (handled by post_save)
        return

    old_shipment = Shipment.objects.get(pk=instance.pk)
    if old_shipment.status != instance.status:
        ShipmentTracking.objects.create(
            shipment=instance,
            status=instance.status,
            location=instance.branch.name if instance.branch else "N/A"
        )
        
        # Notify customer of status change
        notify_customer(
            instance,
            f"Your shipment {instance.tracking_number} status has been updated to {instance.status}."
        )
