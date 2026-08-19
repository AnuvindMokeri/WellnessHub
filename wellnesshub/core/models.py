from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone


ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('vendor', 'Vendor'),
    ('customer', 'User'),
)


class Profile(models.Model):
    """Extends Django's built-in User (== LOGIN table in the synopsis)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f'{self.user.username} ({self.role})'


class Vendor(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor')
    business_name = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name

    @property
    def is_approved(self):
        return self.status == 'approved'


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)
    icon = models.CharField(max_length=10, default='\U0001F33F')  # emoji fallback icon

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=120)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.pk])

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(avg=models.Avg('rating'))['avg']
        return round(agg, 1) if agg else 0

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def in_stock(self):
        return self.stock > 0


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    @property
    def total_price(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f'{self.user.username} - {self.product.name} x{self.quantity}'


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    address = models.CharField(max_length=250)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=30, default='Cash on Delivery')

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f'Order #{self.pk} - {self.user.username}'


class OrderItem(models.Model):
    ITEM_STATUS_CHOICES = Order.STATUS_CHOICES
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    item_status = models.CharField(max_length=20, choices=ITEM_STATUS_CHOICES, default='pending')

    @property
    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        return f'{self.product} x{self.quantity}'


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    review = models.TextField(blank=True)
    review_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-review_date']

    def __str__(self):
        return f'{self.product} - {self.rating}\u2605 by {self.user.username}'


class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    subject = models.CharField(max_length=120, default='General Complaint')
    message = models.TextField()
    reply = models.TextField(blank=True, null=True)
    complaint_date = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-complaint_date']

    @property
    def is_resolved(self):
        return bool(self.reply)

    def __str__(self):
        return f'Complaint #{self.pk} - {self.user.username}'
