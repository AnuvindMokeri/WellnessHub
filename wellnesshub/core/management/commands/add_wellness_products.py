"""
Management command: add_wellness_products

USAGE
-----
  python manage.py add_wellness_products
  python manage.py add_wellness_products --vendor-id 3
  python manage.py add_wellness_products --dry-run

WHAT IT DOES
------------
1. Creates (or reuses) a set of wellness Category rows.
2. Picks a Vendor: the one you pass with --vendor-id, or the
   first Vendor in your DB if you don't pass one.
3. Creates 50 wellness Products, skipping any that already
   exist (matched by name + vendor) so it's safe to re-run.

SETUP
-----
Drop this file at:
  <your_app>/management/commands/add_wellness_products.py

(Django needs the `management/commands/` folder structure, with
an empty __init__.py in both `management/` and `management/commands/`
if they don't already exist.)

Update the two imports below to match your actual app names,
e.g.:
  from shop.models import Category, Product, Vendor
"""

import json
import mimetypes
import os
import urllib.request
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

# ---- EDIT THIS IMPORT to match your project's app layout ----
from core.models import Category, Product, Vendor


CATEGORY_ICONS = {
    "Aromatherapy": "🕯️",
    "Fitness": "🏋️",
    "Mindfulness": "🧘",
    "Sleep": "😴",
    "Supplements": "💊",
    "Nutrition": "🥗",
    "Skincare": "🧴",
    "Bath & Body": "🛁",
    "Recovery": "💆",
    "Lifestyle": "🌿",
}

PRODUCTS = [
    {"name": "Lavender Essential Oil", "category": "Aromatherapy", "price": "14.99", "stock": 120, "description": "Pure lavender essential oil for relaxation and better sleep."},
    {"name": "Eucalyptus Essential Oil", "category": "Aromatherapy", "price": "13.99", "stock": 100, "description": "Refreshing eucalyptus oil to clear the mind and support breathing."},
    {"name": "Peppermint Essential Oil", "category": "Aromatherapy", "price": "12.99", "stock": 110, "description": "Invigorating peppermint oil for energy and focus."},
    {"name": "Ceramic Aroma Diffuser", "category": "Aromatherapy", "price": "34.99", "stock": 60, "description": "Ultrasonic diffuser with warm LED light for a calming atmosphere."},
    {"name": "Scented Candle - Sandalwood", "category": "Aromatherapy", "price": "19.99", "stock": 80, "description": "Soy wax candle with a grounding sandalwood scent."},
    {"name": "Premium Yoga Mat", "category": "Fitness", "price": "39.99", "stock": 75, "description": "Non-slip 6mm yoga mat with carry strap."},
    {"name": "Cork Yoga Block Set", "category": "Fitness", "price": "24.99", "stock": 90, "description": "Set of two eco-friendly cork blocks for yoga support."},
    {"name": "Resistance Band Set", "category": "Fitness", "price": "21.99", "stock": 130, "description": "5-piece resistance band set for strength and mobility training."},
    {"name": "Foam Roller", "category": "Fitness", "price": "27.99", "stock": 70, "description": "High-density foam roller for muscle recovery."},
    {"name": "Adjustable Dumbbells (Pair)", "category": "Fitness", "price": "89.99", "stock": 40, "description": "Space-saving adjustable dumbbells, 5-25 lbs each."},
    {"name": "Meditation Cushion", "category": "Mindfulness", "price": "32.99", "stock": 55, "description": "Buckwheat-filled zafu cushion for seated meditation."},
    {"name": "Guided Meditation Journal", "category": "Mindfulness", "price": "16.99", "stock": 150, "description": "90-day journal with prompts for mindfulness and gratitude."},
    {"name": "Himalayan Salt Lamp", "category": "Mindfulness", "price": "29.99", "stock": 65, "description": "Natural salt crystal lamp for a soothing ambient glow."},
    {"name": "Tibetan Singing Bowl Set", "category": "Mindfulness", "price": "44.99", "stock": 35, "description": "Hand-hammered singing bowl with mallet and cushion, for sound therapy."},
    {"name": "Weighted Blanket 15lb", "category": "Sleep", "price": "69.99", "stock": 50, "description": "Cooling weighted blanket to reduce anxiety and improve sleep."},
    {"name": "Silk Sleep Mask", "category": "Sleep", "price": "15.99", "stock": 140, "description": "100% mulberry silk eye mask, gentle on skin."},
    {"name": "Sleep Sound Machine", "category": "Sleep", "price": "39.99", "stock": 45, "description": "White noise machine with 20 soothing sound options."},
    {"name": "Herbal Sleep Tea", "category": "Sleep", "price": "11.99", "stock": 200, "description": "Chamomile and valerian root tea blend for restful sleep."},
    {"name": "Blue Light Blocking Glasses", "category": "Sleep", "price": "24.99", "stock": 85, "description": "Reduce screen strain and support natural melatonin production."},
    {"name": "Multivitamin Gummies", "category": "Supplements", "price": "18.99", "stock": 180, "description": "Daily multivitamin gummies with essential nutrients."},
    {"name": "Omega-3 Fish Oil Capsules", "category": "Supplements", "price": "22.99", "stock": 160, "description": "High-potency fish oil for heart and brain health."},
    {"name": "Probiotic Complex", "category": "Supplements", "price": "26.99", "stock": 140, "description": "50 billion CFU probiotic blend for gut health."},
    {"name": "Ashwagandha Root Extract", "category": "Supplements", "price": "19.99", "stock": 155, "description": "Adaptogenic herb to help manage stress and support energy."},
    {"name": "Magnesium Glycinate", "category": "Supplements", "price": "17.99", "stock": 170, "description": "Highly absorbable magnesium for muscle relaxation and sleep support."},
    {"name": "Collagen Peptides Powder", "category": "Supplements", "price": "29.99", "stock": 100, "description": "Unflavored collagen powder for skin, hair, and joint support."},
    {"name": "Vitamin D3 + K2 Drops", "category": "Supplements", "price": "15.99", "stock": 165, "description": "Liquid vitamin D3/K2 for bone and immune health."},
    {"name": "Electrolyte Hydration Powder", "category": "Supplements", "price": "24.99", "stock": 120, "description": "Sugar-free electrolyte mix for hydration and recovery."},
    {"name": "Organic Green Tea", "category": "Nutrition", "price": "9.99", "stock": 220, "description": "Loose leaf organic green tea, rich in antioxidants."},
    {"name": "Matcha Powder", "category": "Nutrition", "price": "21.99", "stock": 95, "description": "Ceremonial grade matcha for a calm, focused energy boost."},
    {"name": "Plant-Based Protein Powder", "category": "Nutrition", "price": "34.99", "stock": 110, "description": "Pea and rice protein blend, vanilla flavor."},
    {"name": "Superfood Greens Powder", "category": "Nutrition", "price": "32.99", "stock": 90, "description": "Blend of 20+ vegetables, fruits, and adaptogens."},
    {"name": "Raw Organic Honey", "category": "Nutrition", "price": "13.99", "stock": 130, "description": "Unfiltered raw honey sourced from wildflower fields."},
    {"name": "Facial Jade Roller", "category": "Skincare", "price": "14.99", "stock": 100, "description": "Natural jade roller for facial massage and lymphatic drainage."},
    {"name": "Gua Sha Stone", "category": "Skincare", "price": "12.99", "stock": 105, "description": "Rose quartz gua sha tool for skin tension relief."},
    {"name": "Vitamin C Serum", "category": "Skincare", "price": "27.99", "stock": 90, "description": "Brightening serum with 20% vitamin C and hyaluronic acid."},
    {"name": "Hyaluronic Acid Moisturizer", "category": "Skincare", "price": "24.99", "stock": 85, "description": "Lightweight, deeply hydrating daily face moisturizer."},
    {"name": "Dry Body Brush", "category": "Skincare", "price": "11.99", "stock": 115, "description": "Natural bristle brush for exfoliation and circulation."},
    {"name": "Epsom Salt Soak", "category": "Bath & Body", "price": "10.99", "stock": 150, "description": "Muscle-soothing Epsom salt with eucalyptus and lavender."},
    {"name": "Shea Butter Body Lotion", "category": "Bath & Body", "price": "15.99", "stock": 125, "description": "Deeply moisturizing lotion made with organic shea butter."},
    {"name": "Charcoal Detox Soap Bar", "category": "Bath & Body", "price": "8.99", "stock": 140, "description": "Activated charcoal soap to purify and cleanse skin."},
    {"name": "Bamboo Bath Caddy", "category": "Bath & Body", "price": "29.99", "stock": 55, "description": "Expandable bamboo tray for a spa-style bath experience."},
    {"name": "Essential Oil Bath Bombs (Set of 6)", "category": "Bath & Body", "price": "19.99", "stock": 95, "description": "Fizzing bath bombs infused with relaxing essential oils."},
    {"name": "Acupressure Mat & Pillow Set", "category": "Recovery", "price": "34.99", "stock": 60, "description": "Mat and pillow set to relieve back and neck tension."},
    {"name": "Percussion Massage Gun", "category": "Recovery", "price": "79.99", "stock": 45, "description": "Deep tissue massage gun with 6 attachment heads."},
    {"name": "Compression Socks", "category": "Recovery", "price": "16.99", "stock": 130, "description": "Graduated compression socks for circulation and recovery."},
    {"name": "Cooling Gel Eye Mask", "category": "Recovery", "price": "13.99", "stock": 110, "description": "Reusable gel mask to soothe tired eyes and reduce puffiness."},
    {"name": "Stretching Strap with Loops", "category": "Recovery", "price": "12.99", "stock": 100, "description": "Multi-loop strap for improved flexibility and stretching routines."},
    {"name": "Reusable Water Bottle 1L", "category": "Lifestyle", "price": "22.99", "stock": 160, "description": "Insulated stainless steel bottle, keeps drinks cold 24 hours."},
    {"name": "Desk Standing Mat", "category": "Lifestyle", "price": "39.99", "stock": 50, "description": "Cushioned anti-fatigue mat for standing desks."},
    {"name": "Digital Meditation Timer", "category": "Lifestyle", "price": "18.99", "stock": 80, "description": "Simple timer with gentle chime for meditation and yoga sessions."},
]


class Command(BaseCommand):
    help = "Bulk-creates 50 wellness products (and their categories) for a given vendor."

    def add_arguments(self, parser):
        parser.add_argument(
            "--vendor-id",
            type=int,
            default=None,
            help="ID of the Vendor to attach products to. Defaults to the first Vendor found.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without writing to the database.",
        )
        parser.add_argument(
            "--images-file",
            type=str,
            default=None,
            help=(
                "Path to a JSON file mapping product name -> image URL or local "
                "file path, e.g. images.json (see image_map_template.json)."
            ),
        )

    def handle(self, *args, **options):
        vendor_id = options["vendor_id"]
        dry_run = options["dry_run"]
        images_file = options["images_file"]

        vendor = self._resolve_vendor(vendor_id)
        self.stdout.write(f"Using vendor: {vendor} (id={vendor.pk})")

        image_map = self._load_image_map(images_file)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no data will be written.\n"))

        created_categories = 0
        created_products = 0
        skipped_products = 0

        with transaction.atomic():
            category_cache = {}

            for item in PRODUCTS:
                cat_name = item["category"]

                if cat_name not in category_cache:
                    if dry_run:
                        exists = Category.objects.filter(name=cat_name).exists()
                        category_cache[cat_name] = None
                        if not exists:
                            created_categories += 1
                            self.stdout.write(f"[DRY RUN] Would create category: {cat_name}")
                    else:
                        category, was_created = Category.objects.get_or_create(
                            name=cat_name,
                            defaults={
                                "slug": slugify(cat_name),
                                "icon": CATEGORY_ICONS.get(cat_name, "\U0001F33F"),
                            },
                        )
                        category_cache[cat_name] = category
                        if was_created:
                            created_categories += 1
                            self.stdout.write(f"Created category: {cat_name}")

                if dry_run:
                    already_exists = Product.objects.filter(
                        name=item["name"], vendor=vendor
                    ).exists()
                    if already_exists:
                        skipped_products += 1
                        self.stdout.write(f"[DRY RUN] Skip (exists): {item['name']}")
                    else:
                        created_products += 1
                        self.stdout.write(f"[DRY RUN] Would create: {item['name']} — ${item['price']}")
                    continue

                product, was_created = Product.objects.get_or_create(
                    name=item["name"],
                    vendor=vendor,
                    defaults={
                        "category": category_cache[cat_name],
                        "description": item["description"],
                        "price": Decimal(item["price"]),
                        "stock": item["stock"],
                        "is_active": True,
                    },
                )

                if was_created:
                    created_products += 1
                    self.stdout.write(self.style.SUCCESS(f"Created: {product.name}"))

                    image_source = image_map.get(item["name"])
                    if image_source:
                        self._attach_image(product, image_source)
                else:
                    skipped_products += 1
                    self.stdout.write(f"Skipped (already exists): {product.name}")

            if dry_run:
                # Roll back — nothing should actually be written in a dry run.
                transaction.set_rollback(True)

        self.stdout.write("\n---------------------------------")
        self.stdout.write(f"Categories created: {created_categories}")
        self.stdout.write(f"Products created:   {created_products}")
        self.stdout.write(f"Products skipped:   {skipped_products}")

    def _load_image_map(self, images_file):
        if not images_file:
            return {}

        path = Path(images_file)
        if not path.exists():
            raise CommandError(f"--images-file not found: {images_file}")

        with open(path, "r", encoding="utf-8") as f:
            raw_map = json.load(f)

        # Drop empty/placeholder entries so missing images are just skipped.
        return {name: src for name, src in raw_map.items() if src}

    def _attach_image(self, product, source):
        """Download (http/https) or copy (local path) an image onto a product."""
        try:
            if source.startswith("http://") or source.startswith("https://"):
                req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as response:
                    content = response.read()
                    content_type = response.headers.get_content_type()
                ext = mimetypes.guess_extension(content_type) or ".jpg"
                filename = f"{slugify(product.name)}{ext}"
            else:
                local_path = Path(source)
                if not local_path.exists():
                    self.stdout.write(
                        self.style.WARNING(f"  Image not found, skipping: {source}")
                    )
                    return
                with open(local_path, "rb") as f:
                    content = f.read()
                filename = local_path.name

            product.image.save(filename, ContentFile(content), save=True)
            self.stdout.write(f"  Attached image: {filename}")
        except Exception as exc:  # noqa: BLE001 - report and continue, don't abort the batch
            self.stdout.write(self.style.WARNING(f"  Failed to attach image for {product.name}: {exc}"))

    def _resolve_vendor(self, vendor_id):
        if vendor_id is not None:
            try:
                return Vendor.objects.get(pk=vendor_id)
            except Vendor.DoesNotExist:
                raise CommandError(f"No Vendor found with id={vendor_id}")

        vendor = Vendor.objects.first()
        if vendor is None:
            raise CommandError(
                "No Vendor exists in the database. Create one first, or pass "
                "--vendor-id after creating one."
            )
        return vendor
