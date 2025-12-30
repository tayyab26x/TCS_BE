from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Shipment, CourierStaff, Branch
from .serializers import ShipmentSerializer
from .helpers import assign_shipment_to_courier, update_shipment_status

# ------------------ Customer APIs ------------------

class CreateShipmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ShipmentSerializer(data=request.data)
        if serializer.is_valid():
            shipment = serializer.save(created_by=request.user)
            assign_shipment_to_courier(shipment)
            return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerShipmentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        shipments = Shipment.objects.filter(created_by=request.user)
        serializer = ShipmentSerializer(shipments, many=True)
        return Response(serializer.data)


# ------------------ Courier Staff APIs ------------------

class CourierShipmentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        courier = CourierStaff.objects.get(user=request.user)
        shipments = courier.assigned_shipments.all()
        serializer = ShipmentSerializer(shipments, many=True)
        return Response(serializer.data)


class UpdateShipmentStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        new_status = request.data.get('status')
        if new_status not in [s[0] for s in Shipment.STATUS_CHOICES]:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        update_shipment_status(shipment, new_status)
        return Response(ShipmentSerializer(shipment).data)
