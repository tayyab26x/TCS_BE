# courier/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Shipment, ShipmentTracking
from django.utils import timezone


@receiver(post_save, sender=Shipment)
def create_initial_tracking(sender, instance, created, **kwargs):
    """
    Automatically create a tracking entry when a shipment is first created.
    """
    if created:
        ShipmentTracking.objects.create(
            shipment=instance,
            status=instance.status,
            location=instance.branch.name if instance.branch else ''
        )


@receiver(pre_save, sender=Shipment)
def create_tracking_on_status_change(sender, instance, **kwargs):
    """
    Automatically create a ShipmentTracking entry whenever the shipment status changes.
    """
    if not instance.pk:
        # New shipment, skip (handled by post_save)
        return

    # Get the old shipment from DB
    old_shipment = Shipment.objects.get(pk=instance.pk)
    if old_shipment.status != instance.status:
        ShipmentTracking.objects.create(
            shipment=instance,
            status=instance.status,
            location=instance.branch.name if instance.branch else ''
        )
