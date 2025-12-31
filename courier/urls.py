from django.urls import path
from .views import (
    # Shipment APIs
    CreateShipmentAPIView,
    CustomerShipmentsAPIView,
    CourierShipmentsAPIView,
    UpdateShipmentStatusAPIView,
    TrackShipmentAPIView,
    CancelShipmentAPIView,
    AllShipmentsAPIView,
    
    # User/Role APIs
    CreateUserAPIView,
    ListUsersAPIView,
    UserDetailAPIView,
    ChangePasswordAPIView,
    BranchShipmentsAPIView,
    AssignCourierAPIView,
    ListStaffAPIView,
    ListManagersAPIView,
    
    # Branch APIs
    BranchListAPIView,
    CreateBranchAPIView,
    UpdateBranchAPIView,
    DeleteBranchAPIView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # ---------------- JWT Authentication ----------------
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ---------------- Customer Shipment APIs ----------------
    path('customer/shipments/', CustomerShipmentsAPIView.as_view(), name='customer-shipments'),
    path('customer/shipments/create/', CreateShipmentAPIView.as_view(), name='create-shipment'),
    path('customer/shipments/track/', TrackShipmentAPIView.as_view(), name='track-shipment'),
    path('customer/shipments/<int:shipment_id>/cancel/', CancelShipmentAPIView.as_view(), name='cancel-shipment'),

    # ---------------- Courier Shipment APIs ----------------
    path('courier/shipments/', CourierShipmentsAPIView.as_view(), name='courier-shipments'),
    path('courier/shipments/<int:shipment_id>/update-status/', UpdateShipmentStatusAPIView.as_view(), name='update-shipment-status'),

    # ---------------- User / Role APIs ----------------
    path('users/', ListUsersAPIView.as_view(), name='list-users'),
    path('users/create/', CreateUserAPIView.as_view(), name='create-user'),
    path('users/<int:user_id>/', UserDetailAPIView.as_view(), name='user-detail'),
    path('users/change-password/', ChangePasswordAPIView.as_view(), name='change-password'),

    # ---------------- Manager APIs ----------------
    path('manager/branch/<int:branch_id>/shipments/', BranchShipmentsAPIView.as_view(), name='branch-shipments'),
    path('manager/shipments/<int:shipment_id>/assign-courier/', AssignCourierAPIView.as_view(), name='assign-courier'),

    # ---------------- Super Manager / HR APIs ----------------
    path('super-manager/staff/', ListStaffAPIView.as_view(), name='list-staff'),
    path('super-manager/managers/', ListManagersAPIView.as_view(), name='list-managers'),

    # ---------------- Admin Branch APIs ----------------
    path('admin/branches/', BranchListAPIView.as_view(), name='list-branches'),
    path('admin/branches/create/', CreateBranchAPIView.as_view(), name='create-branch'),
    path('admin/branches/<int:branch_id>/update/', UpdateBranchAPIView.as_view(), name='update-branch'),
    path('admin/branches/<int:branch_id>/delete/', DeleteBranchAPIView.as_view(), name='delete-branch'),

    # ---------------- Admin / Super Manager Shipments ----------------
    path('admin/shipments/', AllShipmentsAPIView.as_view(), name='all-shipments'),
]
