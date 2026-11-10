from pathlib import Path
from PIL import Image, ImageOps
import shutil
import os

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media"
BACKUP_DIR = BASE_DIR / "media_originals_backup"

if not MEDIA_DIR.exists():
    raise SystemExit("Media folder not found!")

BACKUP_DIR.mkdir(exist_ok=True)

MAX_SIZE = (1800, 1800)
QUALITY = 82

total_before = 0
total_after = 0
processed = 0

for image_path in MEDIA_DIR.rglob("*"):

    if not image_path.is_file():
        continue

    if image_path.suffix.lower() not in [".jpg", ".jpeg"]:
        continue

    relative_path = image_path.relative_to(MEDIA_DIR)
    backup_path = BACKUP_DIR / relative_path

    backup_path.parent.mkdir(parents=True, exist_ok=True)

    if not backup_path.exists():
        shutil.copy2(image_path, backup_path)

    original_size = image_path.stat().st_size

    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)

        if image.mode != "RGB":
            image = image.convert("RGB")

        temp_path = image_path.with_name(
            image_path.stem + "_optimised.jpg"
        )

        image.save(
            temp_path,
            "JPEG",
            quality=QUALITY,
            optimize=True,
            progressive=True
        )

    os.replace(temp_path, image_path)

    new_size = image_path.stat().st_size

    total_before += original_size
    total_after += new_size
    processed += 1

    print(
        f"{image_path.name}: "
        f"{original_size / 1024 / 1024:.2f} MB -> "
        f"{new_size / 1024 / 1024:.2f} MB"
    )

print("\nOPTIMISATION COMPLETE")
print(f"Images processed: {processed}")
print(f"Original total: {total_before / 1024 / 1024:.2f} MB")
print(f"Optimised total: {total_after / 1024 / 1024:.2f} MB")

if total_before:
    reduction = (1 - total_after / total_before) * 100
    print(f"Size reduction: {reduction:.1f}%")

print(f"Original backups: {BACKUP_DIR}")