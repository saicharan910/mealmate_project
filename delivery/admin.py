from django.contrib import admin

from .models import Cart, Customer, Item, Order, Restaurant

admin.site.register(Customer)
admin.site.register(Restaurant)
admin.site.register(Item)
admin.site.register(Cart)
admin.site.register(Order)
