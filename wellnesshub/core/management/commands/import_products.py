import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from core.models import Product, Category, Vendor


class Command(BaseCommand):
    help = "Import wellness products from DummyJSON"

    def handle(self, *args, **kwargs):

        # Get an approved vendor
        vendor = Vendor.objects.filter(status="approved").first()

        if not vendor:
            self.stdout.write(
                self.style.ERROR("No approved vendor found.")
            )
            return

        # Get 50 products from DummyJSON
        url = "https://dummyjson.com/products?limit=50"

        response = requests.get(url)
        data = response.json()

        products = data.get("products", [])

        for item in products:

            # Get category name
            category_slug = item.get("category", "wellness")
            category_name = category_slug.replace("-", " ").title()

            # Create category if it doesn't exist
            category, created = Category.objects.get_or_create(
                slug=category_slug,
                defaults={
                    "name": category_name,
                    "icon": "🌿"
                }
            )

            # Skip duplicate products
            if Product.objects.filter(name=item["title"]).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Already exists: {item['title']}"
                    )
                )
                continue

            # Create product
            product = Product.objects.create(
                vendor=vendor,
                category=category,
                name=item["title"],
                description=item.get(
                    "description",
                    "High quality wellness product."
                ),
                price=item.get("price", 0),
                stock=item.get("stock", 0),
                is_active=True
            )

            # Get product image
            image_url = item.get("thumbnail")

            if image_url:
                try:
                    image_response = requests.get(image_url)

                    if image_response.status_code == 200:
                        image_name = (
                            f"{product.pk}_{category_slug}.jpg"
                        )

                        product.image.save(
                            image_name,
                            ContentFile(image_response.content),
                            save=True
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Image failed for {product.name}: {e}"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Added: {product.name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully imported 50 products!"
            )
        )