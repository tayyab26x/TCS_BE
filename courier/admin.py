from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Branch, Shipment, CourierStaff, Payment

# -------------------------------
# CustomUser Admin
# -------------------------------
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)

# -------------------------------
# Branch Admin
# -------------------------------
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'manager', 'contact_number')
    search_fields = ('name', 'location', 'manager__username')
    list_filter = ('manager',)

admin.site.register(Branch, BranchAdmin)

# -------------------------------
# Shipment Admin
# -------------------------------
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'sender_name', 'receiver_name', 'status', 'branch', 'created_by')
    search_fields = ('tracking_number', 'sender_name', 'receiver_name')
    list_filter = ('status', 'branch', 'created_by')
    readonly_fields = ('tracking_number',)  # optional: auto-generate tracking number in save()

    # Automatically generate tracking number if not set
    def save_model(self, request, obj, form, change):
        if not obj.tracking_number:
            import random, string
            obj.tracking_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save_model(request, obj, form, change)

admin.site.register(Shipment, ShipmentAdmin)

# -------------------------------
# CourierStaff Admin
# -------------------------------
class CourierStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch')
    search_fields = ('user__username', 'branch__name')
    filter_horizontal = ('assigned_shipments',)

admin.site.register(CourierStaff, CourierStaffAdmin)

# -------------------------------
# Payment Admin
# -------------------------------
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'payment_type', 'amount', 'status', 'payment_date')
    list_filter = ('payment_type', 'status')
    search_fields = ('shipment__tracking_number',)

admin.site.register(Payment, PaymentAdmin)
