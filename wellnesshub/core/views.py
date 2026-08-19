from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .decorators import admin_required, vendor_required, customer_required
from .forms import (
    CustomerSignupForm, VendorSignupForm, LoginForm, ProductForm,
    ProfileEditForm, VendorProfileEditForm, ReviewForm, ComplaintForm,
    ReplyForm, CheckoutForm,
)
from .models import (
    Profile, Vendor, Category, Product, CartItem, Order, OrderItem,
    Review, Complaint,
)


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def home(request):
    products = Product.objects.filter(is_active=True, vendor__status='approved')
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)

    categories = Category.objects.all()
    featured = products.order_by('-created_at')[:8]

    context = {
        'categories': categories,
        'products': products.order_by('-created_at')[:24],
        'featured': featured,
        'query': query,
        'active_category': category_slug,
        'total_products': products.count(),
    }
    return render(request, 'core/home.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    reviews = product.reviews.select_related('user').all()
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=pk)[:4]
    user_can_review = False
    if request.user.is_authenticated and getattr(request.user, 'profile', None):
        if request.user.profile.role == 'customer':
            has_ordered = OrderItem.objects.filter(
                order__user=request.user, product=product, order__status='delivered'
            ).exists()
            already_reviewed = Review.objects.filter(user=request.user, product=product).exists()
            user_can_review = has_ordered and not already_reviewed
    context = {
        'product': product,
        'reviews': reviews,
        'related': related,
        'user_can_review': user_can_review,
    }
    return render(request, 'core/product_detail.html', context)


def about(request):
    return render(request, 'core/about.html')


# ---------------------------------------------------------------------------
# Auth: signup / login / logout / password
# ---------------------------------------------------------------------------

def customer_signup(request):
    if request.method == 'POST':
        form = CustomerSignupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data['username'], email=data['email'],
                    password=data['password'], first_name=data['name'],
                )
                Profile.objects.create(
                    user=user, role='customer', phone=data['phone'], address=data['address'],
                )
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
    else:
        form = CustomerSignupForm()
    return render(request, 'core/customer_signup.html', {'form': form})


def vendor_signup(request):
    if request.method == 'POST':
        form = VendorSignupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data['username'], email=data['email'],
                    password=data['password'], first_name=data['owner_name'],
                )
                Profile.objects.create(user=user, role='vendor', phone=data['phone'], address=data['address'])
                Vendor.objects.create(
                    user=user, business_name=data['business_name'], owner_name=data['owner_name'],
                    email=data['email'], phone=data['phone'], address=data['address'], status='pending',
                )
            messages.success(request, 'Vendor account created! Your account needs admin approval before you can sell.')
            return redirect('login')
    else:
        form = VendorSignupForm()
    return render(request, 'core/vendor_signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request, username=form.cleaned_data['username'], password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                profile = getattr(user, 'profile', None)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                if profile and profile.role == 'admin':
                    return redirect('admin_dashboard')
                if profile and profile.role == 'vendor':
                    vendor = getattr(user, 'vendor', None)
                    if vendor and vendor.status != 'approved':
                        return redirect('vendor_pending')
                    return redirect('vendor_dashboard')
                return redirect('home')
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('home')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'core/change_password.html', {'form': form})


@login_required
def vendor_pending_view(request):
    vendor = getattr(request.user, 'vendor', None)
    if not vendor:
        return redirect('home')
    if vendor.status == 'approved':
        return redirect('vendor_dashboard')
    return render(request, 'core/vendor_pending.html', {'vendor': vendor})


# ---------------------------------------------------------------------------
# Customer: profile
# ---------------------------------------------------------------------------

@customer_required
def customer_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            request.user.first_name = data['name']
            request.user.email = data['email']
            request.user.save()
            profile.phone = data['phone']
            profile.address = data['address']
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('customer_profile')
    else:
        form = ProfileEditForm(initial={
            'name': request.user.first_name, 'email': request.user.email,
            'phone': profile.phone, 'address': profile.address,
        })
    return render(request, 'core/customer_profile.html', {'form': form})


# ---------------------------------------------------------------------------
# Customer: cart
# ---------------------------------------------------------------------------

@customer_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
    item.save()
    messages.success(request, f'"{product.name}" added to your cart.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@customer_required
def view_cart(request):
    items = CartItem.objects.filter(user=request.user).select_related('product', 'product__vendor')
    total = sum(item.total_price for item in items)
    return render(request, 'core/cart.html', {'items': items, 'total': total})


@customer_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, user=request.user)
    action = request.POST.get('action')
    if action == 'increase' and item.quantity < item.product.stock:
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
            return redirect('view_cart')
        item.save()
    return redirect('view_cart')


@customer_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, user=request.user)
    item.delete()
    messages.info(request, 'Item removed from cart.')
    return redirect('view_cart')


# ---------------------------------------------------------------------------
# Customer: checkout / orders
# ---------------------------------------------------------------------------

@customer_required
def checkout(request):
    items = CartItem.objects.filter(user=request.user).select_related('product', 'product__vendor')
    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('view_cart')

    for item in items:
        if item.quantity > item.product.stock:
            messages.error(request, f'"{item.product.name}" only has {item.product.stock} in stock.')
            return redirect('view_cart')

    total = sum(item.total_price for item in items)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    address=form.cleaned_data['address'],
                    total_amount=total,
                    payment_method=form.cleaned_data['payment_method'],
                    status='confirmed',
                )
                for item in items:
                    OrderItem.objects.create(
                        order=order, product=item.product, vendor=item.product.vendor,
                        quantity=item.quantity, price=item.product.price, item_status='confirmed',
                    )
                    item.product.stock -= item.quantity
                    item.product.save()
                items.delete()
            messages.success(request, f'Order #{order.pk} placed successfully!')
            return redirect('order_detail', pk=order.pk)
    else:
        form = CheckoutForm(initial={'address': request.user.profile.address})

    return render(request, 'core/checkout.html', {'form': form, 'items': items, 'total': total})


@customer_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'core/my_orders.html', {'orders': orders})


@customer_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'core/order_detail.html', {'order': order})


# ---------------------------------------------------------------------------
# Customer: reviews
# ---------------------------------------------------------------------------

@customer_required
def add_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    has_ordered = OrderItem.objects.filter(
        order__user=request.user, product=product, order__status='delivered'
    ).exists()
    if not has_ordered:
        messages.error(request, 'You can only review products from delivered orders.')
        return redirect('product_detail', pk=product.pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review, _ = Review.objects.update_or_create(
                user=request.user, product=product,
                defaults={'rating': form.cleaned_data['rating'], 'review': form.cleaned_data['review']},
            )
            messages.success(request, 'Thanks for your review!')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ReviewForm()
    return render(request, 'core/add_review.html', {'form': form, 'product': product})


# ---------------------------------------------------------------------------
# Customer: complaints
# ---------------------------------------------------------------------------

@customer_required
def my_complaints(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            messages.success(request, 'Your complaint has been submitted.')
            return redirect('my_complaints')
    else:
        form = ComplaintForm()
    complaints = Complaint.objects.filter(user=request.user)
    return render(request, 'core/my_complaints.html', {'form': form, 'complaints': complaints})


# ---------------------------------------------------------------------------
# Vendor
# ---------------------------------------------------------------------------

@vendor_required
def vendor_dashboard(request):
    vendor = request.user.vendor
    products = Product.objects.filter(vendor=vendor)
    order_items = OrderItem.objects.filter(vendor=vendor)
    total_sales = order_items.exclude(item_status='cancelled').aggregate(total=Sum('price'))['total'] or 0
    context = {
        'vendor': vendor,
        'product_count': products.count(),
        'low_stock_count': products.filter(stock__lt=5).count(),
        'order_count': order_items.count(),
        'pending_orders': order_items.filter(item_status__in=['pending', 'confirmed']).count(),
        'total_sales': total_sales,
        'recent_orders': order_items.select_related('order', 'product').order_by('-order__order_date')[:6],
    }
    return render(request, 'core/vendor_dashboard.html', context)


@vendor_required
def vendor_profile(request):
    vendor = request.user.vendor
    if request.method == 'POST':
        form = VendorProfileEditForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Business profile updated.')
            return redirect('vendor_profile')
    else:
        form = VendorProfileEditForm(instance=vendor)
    return render(request, 'core/vendor_profile.html', {'form': form, 'vendor': vendor})


@vendor_required
def vendor_products(request):
    products = Product.objects.filter(vendor=request.user.vendor)
    return render(request, 'core/vendor_products.html', {'products': products})


@vendor_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user.vendor
            product.save()
            messages.success(request, f'Product "{product.name}" added.')
            return redirect('vendor_products')
    else:
        form = ProductForm()
    return render(request, 'core/product_form.html', {'form': form, 'title': 'Add Product'})


@vendor_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated.')
            return redirect('vendor_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})


@vendor_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, vendor=request.user.vendor)
    product.delete()
    messages.info(request, 'Product removed.')
    return redirect('vendor_products')


@vendor_required
def vendor_orders(request):
    order_items = OrderItem.objects.filter(vendor=request.user.vendor).select_related('order', 'product', 'order__user')
    return render(request, 'core/vendor_orders.html', {'order_items': order_items})


@vendor_required
def update_order_item_status(request, item_id):
    item = get_object_or_404(OrderItem, pk=item_id, vendor=request.user.vendor)
    if request.method == 'POST':
        new_status = request.POST.get('item_status')
        if new_status in dict(OrderItem.ITEM_STATUS_CHOICES):
            item.item_status = new_status
            item.save()
            messages.success(request, f'Order item status updated to "{item.get_item_status_display()}".')
    return redirect('vendor_orders')


@vendor_required
def vendor_sales_report(request):
    vendor = request.user.vendor
    order_items = OrderItem.objects.filter(vendor=vendor).exclude(item_status='cancelled')
    by_product = (
        order_items.values('product__name')
        .annotate(units_sold=Sum('quantity'), revenue=Sum('price'))
        .order_by('-revenue')
    )
    total_revenue = order_items.aggregate(total=Sum('price'))['total'] or 0
    total_units = order_items.aggregate(total=Sum('quantity'))['total'] or 0
    return render(request, 'core/vendor_sales_report.html', {
        'by_product': by_product, 'total_revenue': total_revenue, 'total_units': total_units,
    })


@vendor_required
def vendor_reviews(request):
    reviews = Review.objects.filter(product__vendor=request.user.vendor).select_related('product', 'user')
    return render(request, 'core/vendor_reviews.html', {'reviews': reviews})


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@admin_required
def admin_dashboard(request):
    context = {
        'user_count': Profile.objects.filter(role='customer').count(),
        'vendor_count': Vendor.objects.count(),
        'pending_vendor_count': Vendor.objects.filter(status='pending').count(),
        'product_count': Product.objects.count(),
        'order_count': Order.objects.count(),
        'complaint_count': Complaint.objects.filter(reply__isnull=True).count(),
        'total_sales': OrderItem.objects.exclude(item_status='cancelled').aggregate(total=Sum('price'))['total'] or 0,
        'recent_orders': Order.objects.select_related('user').order_by('-order_date')[:6],
        'pending_vendors': Vendor.objects.filter(status='pending')[:5],
    }
    return render(request, 'core/admin_dashboard.html', context)


@admin_required
def manage_users(request):
    profiles = Profile.objects.filter(role='customer').select_related('user')
    return render(request, 'core/manage_users.html', {'profiles': profiles})


@admin_required
def toggle_user_active(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f'{user.username} is now {"active" if user.is_active else "blocked"}.')
    return redirect('manage_users')


@admin_required
def manage_vendors(request):
    vendors = Vendor.objects.select_related('user').all()
    return render(request, 'core/manage_vendors.html', {'vendors': vendors})


@admin_required
def update_vendor_status(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    action = request.POST.get('action')
    if action == 'approve':
        vendor.status = 'approved'
        messages.success(request, f'{vendor.business_name} approved.')
    elif action == 'reject':
        vendor.status = 'rejected'
        messages.warning(request, f'{vendor.business_name} rejected.')
    elif action == 'block':
        vendor.user.is_active = False
        vendor.user.save()
        messages.info(request, f'{vendor.business_name} account blocked.')
    vendor.save()
    return redirect('manage_vendors')


@admin_required
def manage_products(request):
    products = Product.objects.select_related('vendor', 'category').all()
    return render(request, 'core/manage_products.html', {'products': products})


@admin_required
def admin_remove_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = False
    product.save()
    messages.info(request, f'"{product.name}" was deactivated.')
    return redirect('manage_products')


@admin_required
def manage_categories(request):
    categories = Category.objects.annotate(product_count=Count('products'))
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', '\U0001F33F').strip() or '\U0001F33F'
        if name:
            from django.utils.text import slugify
            Category.objects.get_or_create(name=name, defaults={'slug': slugify(name), 'icon': icon})
            messages.success(request, f'Category "{name}" added.')
            return redirect('manage_categories')
    return render(request, 'core/manage_categories.html', {'categories': categories})


@admin_required
def manage_orders(request):
    orders = Order.objects.select_related('user').prefetch_related('items').all()
    return render(request, 'core/manage_orders.html', {'orders': orders})


@admin_required
def admin_sales_report(request):
    order_items = OrderItem.objects.exclude(item_status='cancelled')
    by_vendor = (
        order_items.values('vendor__business_name')
        .annotate(units_sold=Sum('quantity'), revenue=Sum('price'))
        .order_by('-revenue')
    )
    by_category = (
        order_items.values('product__category__name')
        .annotate(units_sold=Sum('quantity'), revenue=Sum('price'))
        .order_by('-revenue')
    )
    total_revenue = order_items.aggregate(total=Sum('price'))['total'] or 0
    return render(request, 'core/admin_sales_report.html', {
        'by_vendor': by_vendor, 'by_category': by_category, 'total_revenue': total_revenue,
    })


@admin_required
def manage_complaints(request):
    complaints = Complaint.objects.select_related('user').all()
    return render(request, 'core/manage_complaints.html', {'complaints': complaints})


@admin_required
def reply_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            complaint.reply = form.cleaned_data['reply']
            complaint.replied_at = timezone.now()
            complaint.save()
            messages.success(request, 'Reply sent to the customer.')
            return redirect('manage_complaints')
    else:
        form = ReplyForm()
    return render(request, 'core/reply_complaint.html', {'form': form, 'complaint': complaint})
