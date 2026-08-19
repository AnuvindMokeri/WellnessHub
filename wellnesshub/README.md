# WellnessHub

A multi-vendor e-commerce web application for wellness products (skincare,
fitness, herbal/Ayurvedic, healthy snacks, personal care and supplements),
built with **Python (Django)**, matching the synopsis submitted for the
IGNOU BCA project **"WellnessHub"** — three role-based modules (Admin,
Vendor, User), matching the ER diagram, data flow diagrams and table
structures in the synopsis.

## Features

**User (Customer)**
Signup / login, view & edit profile, browse & search products by category,
add to cart, view cart, checkout & place orders, track order status, rate
& review delivered products, raise complaints and view admin replies,
change password.

**Vendor**
Signup (requires admin approval) / login, view & edit business profile,
full product management (add / edit / delete, stock & pricing), view
incoming orders and update their status, view a sales report (revenue and
units sold per product), view ratings & reviews left on their products,
change password.

**Admin**
Central dashboard with key stats, manage users (block/unblock), approve or
reject vendor applications, manage the product catalog and categories,
view all orders, a marketplace-wide sales report (by vendor and by
category), view and reply to customer complaints, change password.

## Tech stack

- **Backend:** Python 3, Django
- **Database:** SQLite by default (zero setup) — easily switched to MySQL
  (see `wellnesshub/settings.py`, matching the synopsis's proposed stack)
- **Frontend:** Django templates, HTML5, CSS3 (custom design system, no
  frameworks), vanilla JS where needed

## Getting started

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py makemigrations
python manage.py migrate

# 4. (Optional but recommended) seed demo data — an admin account,
#    3 demo vendors, a demo customer, categories and sample products
python manage.py seed_demo

# 5. Run the development server
python manage.py runserver
```

Then open **http://127.0.0.1:8000/** in your browser.

### Demo accounts (created by `seed_demo`)

| Role     | Username    | Password       |
|----------|-------------|----------------|
| Admin    | `admin`     | `admin12345`   |
| Vendor   | `greenleaf` | `vendor12345`  |
| Vendor   | `fitgear`   | `vendor12345`  |
| Vendor   | `purelife` (pending approval) | `vendor12345` |
| Customer | `customer`  | `customer12345`|

If you'd rather start from a completely empty database, skip step 4 and
sign up through the website (`/signup/` for customers, `/vendor/signup/`
for vendors), and create an admin with:

```bash
python manage.py createsuperuser
```
Then, in the Django shell (`python manage.py shell`), give that user an
admin `Profile`:
```python
from django.contrib.auth.models import User
from core.models import Profile
u = User.objects.get(username='your_admin_username')
Profile.objects.create(user=u, role='admin')
```

## Switching to MySQL

The synopsis's hardware/software section lists MySQL as the backend
database. To switch:

1. `pip install mysqlclient`
2. Create a database: `CREATE DATABASE wellnesshub;`
3. In `wellnesshub/settings.py`, comment out the SQLite `DATABASES` block
   and uncomment the MySQL block, filling in your credentials.
4. Re-run `python manage.py migrate`.

## Project structure

```
wellnesshub/
├── manage.py
├── requirements.txt
├── wellnesshub/          # project settings, root urls
├── core/                 # the whole app
│   ├── models.py         # Profile, Vendor, Category, Product, CartItem,
│   │                       Order, OrderItem, Review, Complaint
│   ├── views.py          # public / customer / vendor / admin views
│   ├── forms.py
│   ├── decorators.py     # role-based access control
│   ├── urls.py
│   ├── management/commands/seed_demo.py
│   ├── templates/core/   # all HTML templates
│   └── static/core/      # CSS
└── media/                # uploaded product images
```

## Notes for your project report

- The **ER diagram** in your synopsis (Login, Users, Vendors, Products,
  Cart, Orders, Reviews, Complaints, Sales Report) maps directly onto the
  models in `core/models.py` — `Profile` plays the role of the `Login` +
  role-linking table, `OrderItem` links Orders ↔ Products ↔ Vendors so
  per-vendor sales reports can be generated as described in your
  synopsis's "Report Generation" section.
- Role-based access control (Admin / Vendor / User) is implemented via
  `core/decorators.py`, matching the "role-based access control" objective
  in your synopsis.
- Screenshots for your report: run the server, log in as each of the
  three roles using the demo accounts above, and capture the dashboards,
  product listing, cart/checkout flow, and admin approval screens.
