from django.contrib import admin
from .models import RealtyAd


class RealtyAdAdmin(admin.ModelAdmin):
    pass


admin.site.register(RealtyAd, RealtyAdAdmin)
