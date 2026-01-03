from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Shipment, CourierStaff, Branch, CustomUser
from .serializers import (
    ShipmentSerializer, UserSerializer, ChangePasswordSerializer,
    BranchSerializer, MyTokenObtainPairSerializer
)
from .helpers import assign_shipment_to_courier, update_shipment_status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny


# Custom JWT login view using email instead of username
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# -------------------------
# Create new user (Admin / Super Manager)
# -------------------------
class CreateUserAPIView(APIView):
    permission_classes = [AllowAny]  # Public access

    def post(self, request):
        data = request.data.copy()

        # Default role to customer if not provided
        if 'role' not in data:
            data['role'] = 'customer'

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# Get all users or filter by role
# -------------------------
class ListUsersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['admin', 'super_manager']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        role = request.query_params.get('role', None)
        if role:
            users = CustomUser.objects.filter(role=role)
        else:
            users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


# -------------------------
# Retrieve, Update, Delete a single user
# -------------------------
class UserDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, user_id):
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None

    def get(self, request, user_id):
        user = self.get_object(user_id)
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, user_id):
        if request.user.role not in ['admin', 'super_manager'] and request.user.id != user_id:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object(user_id)
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        if request.user.role not in ['admin', 'super_manager']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object(user_id)
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


# -------------------------
# Change own password
# -------------------------
class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------ Customer APIs ------------------

class CreateShipmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'customer':
            return Response({'error': 'Only customers can create shipments'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ShipmentSerializer(data=request.data)
        if serializer.is_valid():
            shipment = serializer.save(created_by=request.user)
            assign_shipment_to_courier(shipment)
            return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerShipmentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'customer':
            return Response({'error': 'Only customers can view their shipments'}, status=status.HTTP_403_FORBIDDEN)

        shipments = Shipment.objects.filter(created_by=request.user).order_by('-pickup_date')
        serializer = ShipmentSerializer(shipments, many=True)
        return Response(serializer.data)


# ------------------ Courier Staff APIs ------------------

class CourierShipmentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'staff':
            return Response({'error': 'Only courier staff can access this'}, status=status.HTTP_403_FORBIDDEN)
        try:
            courier = CourierStaff.objects.get(user=request.user)
        except CourierStaff.DoesNotExist:
            return Response({'error': 'Courier profile not found'}, status=status.HTTP_404_NOT_FOUND)

        shipments = courier.assigned_shipments.all().order_by('-pickup_date')
        serializer = ShipmentSerializer(shipments, many=True)
        return Response(serializer.data)


class UpdateShipmentStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, shipment_id):
        if request.user.role not in ['staff', 'manager']:
            return Response({'error': 'You do not have permission to update shipment status'}, status=status.HTTP_403_FORBIDDEN)

        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        new_status = request.data.get('status')
        if new_status not in [s[0] for s in Shipment.STATUS_CHOICES]:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        update_shipment_status(shipment, new_status)
        return Response(ShipmentSerializer(shipment).data)



# -------------------------
# Manager APIs: Branch Shipments & Assign Courier
# -------------------------
class BranchShipmentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, branch_id):
        if request.user.role not in ['manager', 'super_manager', 'admin']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)

        # Manager can only see their own branch
        if request.user.role == 'manager' and branch.manager != request.user:
            return Response({'error': 'You can only view your own branch shipments'}, status=status.HTTP_403_FORBIDDEN)

        shipments = Shipment.objects.filter(branch=branch).order_by('-pickup_date')
        serializer = ShipmentSerializer(shipments, many=True)
        return Response(serializer.data)


class AssignCourierAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, shipment_id):
        if request.user.role not in ['manager', 'super_manager', 'admin']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        courier_id = request.data.get('courier_id')
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            courier = CourierStaff.objects.get(id=courier_id, branch=shipment.branch)
        except CourierStaff.DoesNotExist:
            return Response({'error': 'Courier not found in this branch'}, status=status.HTTP_404_NOT_FOUND)

        shipment.courier = courier
        shipment.status = 'out_for_delivery'
        shipment.save()
        courier.assigned_shipments.add(shipment)

        return Response(ShipmentSerializer(shipment).data)


# -------------------------
# Super Manager / HR APIs: Staff & Manager Management
# -------------------------
class ListStaffAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['super_manager', 'admin']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        staff = CustomUser.objects.filter(role='staff')
        serializer = UserSerializer(staff, many=True)
        return Response(serializer.data)


class ListManagersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['super_manager', 'admin']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        managers = CustomUser.objects.filter(role='manager')
        serializer = UserSerializer(managers, many=True)
        return Response(serializer.data)


# -------------------------
# Admin APIs: All Branches & Users
# -------------------------
class BranchListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        branches = Branch.objects.all()
        serializer = BranchSerializer(branches, many=True)
        return Response(serializer.data)



class TrackShipmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tracking_number = request.query_params.get('tracking_number')
        if not tracking_number:
            return Response({'error': 'Tracking number is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            shipment = Shipment.objects.get(tracking_number=tracking_number)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=status.HTTP_404_NOT_FOUND)

        # Only allow customer to track their own shipment, or staff/admin
        if request.user.role == 'customer' and shipment.created_by != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ShipmentSerializer(shipment)
        return Response(serializer.data)


class CancelShipmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, shipment_id):
        if request.user.role != 'customer':
            return Response({'error': 'Only customers can cancel shipments'}, status=status.HTTP_403_FORBIDDEN)

        try:
            shipment = Shipment.objects.get(id=shipment_id, created_by=request.user)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=status.HTTP_404_NOT_FOUND)

        if shipment.status in ['picked_up', 'out_for_delivery', 'delivered']:
            return Response({'error': 'Cannot cancel shipment at this stage'}, status=status.HTTP_400_BAD_REQUEST)

        shipment.status = 'cancelled'
        shipment.save()
        return Response({'message': 'Shipment cancelled successfully'}, status=status.HTTP_200_OK)


class CreateBranchAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateBranchAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, branch_id):
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BranchSerializer(branch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteBranchAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, branch_id):
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)

        branch.delete()
        return Response({'message': 'Branch deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class AllShipmentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['admin', 'super_manager']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        status_filter = request.query_params.get('status')
        branch_filter = request.query_params.get('branch_id')
        courier_filter = request.query_params.get('courier_id')

        shipments = Shipment.objects.all()

        if status_filter:
            shipments = shipments.filter(status=status_filter)
        if branch_filter:
            shipments = shipments.filter(branch_id=branch_filter)
        if courier_filter:
            shipments = shipments.filter(courier_id=courier_filter)

        serializer = ShipmentSerializer(shipments, many=True)
        return Response(serializer.data)
