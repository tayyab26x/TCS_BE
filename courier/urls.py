from django.urls import path
from .views import (
    CreateShipmentAPIView,
    CustomerShipmentsAPIView,
    CourierShipmentsAPIView,
    UpdateShipmentStatusAPIView,
)

urlpatterns = [
    path('customer/shipments/', CustomerShipmentsAPIView.as_view(), name='customer-shipments'),
    path('customer/shipments/create/', CreateShipmentAPIView.as_view(), name='create-shipment'),
    path('courier/shipments/', CourierShipmentsAPIView.as_view(), name='courier-shipments'),
    path('courier/shipments/<int:shipment_id>/update-status/', UpdateShipmentStatusAPIView.as_view(), name='update-shipment-status'),
]
