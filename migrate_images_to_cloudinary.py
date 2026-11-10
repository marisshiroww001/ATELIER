
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from store.models import Product, ProductImage


storage = storages["default"]
migrated = 0
skipped = 0
failed = 0


def migrate_images(model):
    global migrated, skipped, failed

    for obj in model.objects.exclude(image=""):
        old_name = obj.image.name
        local_path = Path(settings.MEDIA_ROOT) / old_name

        if not local_path.exists():
            print(f"SKIPPED — local file missing: {old_name}")
            skipped += 1
            continue

        try:
            # Upload under the original filename in a dedicated folder.
            destination = f"atelier/{old_name}"

            if storage.exists(destination):
                new_name = destination
                print(f"ALREADY EXISTS: {destination}")
            else:
                with local_path.open("rb") as file:
                    new_name = storage.save(
                        destination,
                        ContentFile(file.read())
                    )

            # Update only the database field, without re-uploading.
            model.objects.filter(pk=obj.pk).update(image=new_name)

            print(f"MIGRATED: {old_name} -> {new_name}")
            migrated += 1

        except Exception as error:
            print(f"FAILED: {old_name} — {error}")
            failed += 1


print("Starting product image migration...")
migrate_images(Product)

print("\nStarting gallery image migration...")
migrate_images(ProductImage)

print("\nMIGRATION SUMMARY")
print(f"Migrated: {migrated}")
print(f"Skipped: {skipped}")
print(f"Failed: {failed}")
