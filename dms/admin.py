from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, Document, DocumentRouting, DocumentLog, Notification


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'role', 'department', 'email']
    list_filter = ['role', 'department']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Department', {'fields': ('role', 'department')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'title', 'source', 'status', 'classification', 'created_by', 'created_at']
    list_filter = ['status', 'source', 'classification']
    search_fields = ['title', 'reference_number']


@admin.register(DocumentLog)
class DocumentLogAdmin(admin.ModelAdmin):
    list_display = ['document', 'action', 'user', 'timestamp']
    list_filter = ['action']


@admin.register(DocumentRouting)
class DocumentRoutingAdmin(admin.ModelAdmin):
    list_display = ['document', 'from_department', 'to_department', 'forwarded_by', 'forwarded_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'message', 'is_read', 'created_at']
