from django.contrib import admin
from .models import Profile, Vendor, Category, Product, CartItem, Order, OrderItem, Review, Complaint

admin.site.register(Profile)
admin.site.register(Vendor)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Complaint)
