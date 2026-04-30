import json
import hashlib
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from django.db import transaction
from accounts.models import College


class Command(BaseCommand):
    help = "Import institutions from JSON file into College model efficiently"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="institutions.json",
            help="Path to the institutions JSON file (default: institutions.json)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=2000,
            help="Batch size for bulk_create (default: 2000)",
        )

    def normalize_name(self, name):
        """
        Normalize college name for deduplication:
        - lowercase
        - strip leading/trailing spaces
        - collapse multiple spaces into one
        - allow only: a-z, 0-9, space, '-', '&', '.'
        """
        if not name:
            return ""
        # Lowercase and strip
        normalized = name.lower().strip()
        # Collapse multiple spaces
        normalized = " ".join(normalized.split())
        # Allow only: a-z, 0-9, space, '-', '&', '.'
        normalized = "".join(
            c for c in normalized if c.isalnum() or c in " -&."
        )
        return normalized

    def generate_slug(self, safe_normalized, city, state, existing_slugs):
        """
        Generate unique slug with collision handling.
        Hash suffix is based on md5(safe_normalized|city|state).
        If duplicate slug occurs, append short hash (first 6 chars of md5).
        """
        # Base slug truncated to 190 chars to leave room for hash suffix
        base_slug = slugify(safe_normalized)[:190]
        slug = base_slug

        # Define hash_suffix BEFORE loop (use | separator to prevent collisions)
        hash_input = f"{safe_normalized}|{city}|{state}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:6]

        # Handle collisions in-memory
        counter = 0
        while slug in existing_slugs:
            if counter == 0:
                # First collision: add hash
                slug = f"{base_slug}-{hash_suffix}"
            else:
                # Further collisions: add counter
                slug = f"{base_slug}-{hash_suffix}-{counter}"
            counter += 1

        return slug

    def handle(self, *args, **options):
        file_path = options["file"]
        batch_size = options["batch_size"]

        # Check if file exists
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                institutions = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in file: {e}")

        if not isinstance(institutions, list):
            raise CommandError("JSON file must contain a list of institutions")

        total_records = len(institutions)
        self.stdout.write(f"Total records read: {total_records}")

        # Pre-process: deduplicate by (normalized_name, city, state) in-memory
        seen_keys = set()
        colleges_to_create = []

        for idx, inst in enumerate(institutions):
            # Handle missing/invalid fields safely
            raw_name = inst.get("name", "")
            if not raw_name or not isinstance(raw_name, str):
                continue

            normalized = self.normalize_name(raw_name)
            if not normalized:
                continue

            # Extract fields safely
            aishe_code = inst.get("aishe_code", "")
            state = inst.get("state", "")
            district = inst.get("district", "")  # Maps to city

            city = district.strip() if district else None
            state_stripped = state.strip() if state else None

            # Skip duplicates (keep first occurrence) based on (normalized_name, city, state)
            dedup_key = (normalized, city, state_stripped)
            if dedup_key in seen_keys:
                continue

            seen_keys.add(dedup_key)

            # Safe truncation for DB field length limits (max 200 chars)
            MAX_DB_LEN = 200
            safe_name = raw_name.strip().title()[:MAX_DB_LEN]
            safe_normalized = normalized[:MAX_DB_LEN]

            colleges_to_create.append(
                {
                    "name": safe_name,
                    "normalized_name": safe_normalized,
                    "aishe_code": aishe_code.strip() if aishe_code else None,
                    "state": state_stripped,
                    "city": city,
                    "is_verified": True,
                }
            )

        # Load existing (normalized_name, city, state) from DB to skip duplicates
        existing_records = set(
            College.objects.values_list("normalized_name", "city", "state")
        )
        self.stdout.write(
            f"Existing records in DB: {len(existing_records)}"
        )

        # Filter out records that already exist in DB (track count, no per-record logging)
        colleges_filtered = []
        skipped_existing = 0
        for college_data in colleges_to_create:
            key = (college_data["normalized_name"], college_data["city"], college_data["state"])
            if key not in existing_records:
                colleges_filtered.append(college_data)
            else:
                skipped_existing += 1

        colleges_to_create = colleges_filtered

        # Load existing slugs from DB for collision-free slug generation
        existing_slugs = set(
            College.objects.values_list("slug", flat=True)
        )
        for college_data in colleges_to_create:
            slug = self.generate_slug(
                college_data["normalized_name"],
                college_data["city"],
                college_data["state"],
                existing_slugs
            )
            college_data["slug"] = slug
            existing_slugs.add(slug)  # Track in-memory for subsequent collisions

        total_to_insert = len(colleges_to_create)
        total_skipped = total_records - total_to_insert

        self.stdout.write(
            f"After deduplication: {total_to_insert} unique records to insert"
        )
        self.stdout.write(f"Skipped (duplicates/invalid): {total_skipped}")
        self.stdout.write(f"Skipped existing records: {skipped_existing}")
        self.stdout.write(
            f"Batch size: {batch_size} | Total batches: {(total_to_insert + batch_size - 1) // batch_size}"
        )

        # Bulk insert in batches
        inserted_count = 0

        with transaction.atomic():
            for i in range(0, len(colleges_to_create), batch_size):
                batch = colleges_to_create[i : i + batch_size]

                # Create College instances
                batch_instances = [
                    College(
                        name=data["name"],
                        normalized_name=data["normalized_name"],
                        slug=data["slug"],
                        aishe_code=data["aishe_code"],
                        city=data["city"],
                        state=data["state"],
                        is_verified=data["is_verified"],
                    )
                    for data in batch
                ]

                # Bulk create with ignore_conflicts for safety
                created = College.objects.bulk_create(
                    batch_instances,
                    batch_size=len(batch_instances),
                    ignore_conflicts=True,
                )
                inserted_count += len(created)

                # Progress update
                self.stdout.write(
                    f"Processed batch {i // batch_size + 1}: "
                    f"inserted {len(created)} records (total: {inserted_count})"
                )

        # Final summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(self.style.SUCCESS("IMPORT COMPLETED SUCCESSFULLY"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS(f"Total records read: {total_records}"))
        self.stdout.write(self.style.SUCCESS(f"Total inserted: {inserted_count}"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Total skipped (duplicates/invalid): {total_records - inserted_count}"
            )
        )
        self.stdout.write(self.style.SUCCESS("=" * 50))
