# courier/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Shipment, ShipmentTracking, CourierStaff
from .helpers import assign_shipment_to_courier, calculate_eta, notify_customer


# ---------------------------
# Unified shipment automation
# ---------------------------
@receiver(post_save, sender=Shipment)
def shipment_automation(sender, instance, created, **kwargs):
    """
    Handles all shipment-related automation:
    - Initial tracking creation
    - Courier assignment
    - Courier availability update
    - ETA calculation
    - Customer notifications
    """
    # ----------------- On Creation -----------------
    if created:
        ShipmentTracking.objects.create(
            shipment=instance,
            status=instance.status,
            location=instance.branch.name if instance.branch else None
        )
        assign_shipment_to_courier(instance)
        calculate_eta(instance)
        notify_customer(
            instance,
            f"Your shipment {instance.tracking_number} has been created and is currently {instance.status}."
        )

    # ----------------- On Status Update -----------------
    else:
        try:
            old_shipment = Shipment.objects.get(pk=instance.pk)
        except Shipment.DoesNotExist:
            return

        if old_shipment.status != instance.status:
            ShipmentTracking.objects.create(
                shipment=instance,
                status=instance.status,
                location=instance.branch.name if instance.branch else None
            )

            if instance.courier:
                if instance.status in ['out_for_delivery', 'pending', 'in_warehouse']:
                    instance.courier.is_available = False
                else:  # delivered or cancelled
                    instance.courier.is_available = True
                instance.courier.save()

            calculate_eta(instance)

            notify_customer(
                instance,
                f"Your shipment {instance.tracking_number} status has been updated to {instance.status}."
            )
