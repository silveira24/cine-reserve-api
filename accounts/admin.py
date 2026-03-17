from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class UserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_staff')
    
    add_fieldsets =  (
        (None, {'fields': ('email',)}),
    ) + UserAdmin.add_fieldsets 
admin.site.register(User, UserAdmin)