from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import Profile, Vendor, Category, Product


class Command(BaseCommand):
    help = 'Seeds the database with a demo admin, vendors, categories and products.'

    def handle(self, *args, **options):
        # --- Admin -----------------------------------------------------
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@wellnesshub.local', 'admin12345')
            admin.first_name = 'Site Admin'
            admin.save()
            Profile.objects.create(user=admin, role='admin', phone='9999999999')
            self.stdout.write(self.style.SUCCESS('Created admin -> username: admin / password: admin12345'))
        else:
            self.stdout.write('Admin already exists, skipping.')

        # --- Categories --------------------------------------------------
        categories_data = [
            ('Skincare', '\U0001F9F4'), ('Fitness', '\U0001F3CB'), ('Herbal & Ayurvedic', '\U0001F33F'),
            ('Healthy Snacks', '\U0001F96C'), ('Personal Care', '\U0001F6C1'), ('Supplements', '\U0001F48A'),
        ]
        categories = {}
        for name, icon in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'slug': slugify(name), 'icon': icon})
            categories[name] = cat
        self.stdout.write(self.style.SUCCESS(f'Ensured {len(categories)} categories.'))

        # --- Vendors -------------------------------------------------------
        vendors_data = [
            ('greenleaf', 'GreenLeaf Naturals', 'Anita Menon', '9847012345', 'approved'),
            ('fitgear', 'FitGear Essentials', 'Rohan Kapoor', '9847012346', 'approved'),
            ('purelife', 'PureLife Organics', 'Sara Thomas', '9847012347', 'pending'),
        ]
        vendors = {}
        for username, business, owner, phone, status in vendors_data:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username, f'{username}@wellnesshub.local', 'vendor12345', first_name=owner)
                Profile.objects.create(user=user, role='vendor', phone=phone, address='Kannur, Kerala')
                vendor = Vendor.objects.create(
                    user=user, business_name=business, owner_name=owner,
                    email=f'{username}@wellnesshub.local', phone=phone,
                    address='Kannur, Kerala', status=status,
                )
            else:
                vendor = User.objects.get(username=username).vendor
            vendors[username] = vendor
        self.stdout.write(self.style.SUCCESS(f'Ensured {len(vendors)} vendors. (password for all: vendor12345)'))

        # --- Demo customer ---------------------------------------------
        if not User.objects.filter(username='customer').exists():
            cust = User.objects.create_user('customer', 'customer@wellnesshub.local', 'customer12345', first_name='Demo Customer')
            Profile.objects.create(user=cust, role='customer', phone='9847099999', address='Kozhikode, Kerala')
            self.stdout.write(self.style.SUCCESS('Created demo customer -> username: customer / password: customer12345'))

        # --- Products -------------------------------------------------
        products_data = [
            ('greenleaf', 'Skincare', 'Neem & Turmeric Face Wash', 'A gentle daily face wash with neem and turmeric extracts for clear, calm skin.', 249, 60),
            ('greenleaf', 'Herbal & Ayurvedic', 'Cold-Pressed Coconut Oil (500ml)', 'Traditionally cold-pressed virgin coconut oil for skin, hair and cooking.', 399, 40),
            ('greenleaf', 'Personal Care', 'Aloe Vera Gel (200g)', 'Soothing 99% pure aloe vera gel for skin and hair care.', 199, 80),
            ('fitgear', 'Fitness', 'Resistance Band Set (5 pcs)', 'Latex resistance bands of varying strength for home workouts.', 599, 35),
            ('fitgear', 'Fitness', 'Yoga Mat — Extra Thick', '6mm anti-slip yoga mat, ideal for yoga and floor exercises.', 899, 25),
            ('fitgear', 'Supplements', 'Whey Protein — Chocolate (1kg)', '24g protein per serving, low sugar, great post-workout recovery.', 1899, 20),
            ('greenleaf', 'Healthy Snacks', 'Roasted Makhana (Foxnut) 150g', 'Lightly roasted and seasoned fox nuts — a guilt-free crunchy snack.', 149, 100),
            ('fitgear', 'Healthy Snacks', 'Mixed Dry Fruits Trail Mix 250g', 'Almonds, cashews, raisins and walnuts blended for on-the-go energy.', 349, 55),
        ]
        created = 0
        for vendor_key, cat_name, name, desc, price, stock in products_data:
            vendor = vendors.get(vendor_key)
            if vendor and not Product.objects.filter(vendor=vendor, name=name).exists():
                Product.objects.create(
                    vendor=vendor, category=categories[cat_name], name=name, description=desc,
                    price=Decimal(str(price)), stock=stock,
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} demo products.'))
        self.stdout.write(self.style.SUCCESS('Seed complete!'))
