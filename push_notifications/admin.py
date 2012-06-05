from django.contrib import admin
from models import IDevice

class IDeviceAdmin(admin.ModelAdmin):
    title = 'IDevice'

    list_display = ('token', 'app_id')
    list_filter = ('app_id',)
    readonly_fields = ('person',)
    search_fields = ('person__user__first_name', 'person__user__last_name', 
                        'person__user__email',)

admin.site.register(IDevice, IDeviceAdmin)
