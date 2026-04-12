import redis
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import Room

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up stale Redis presence sets for rooms that no longer have active connections'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting Redis presence cleanup...')

        try:
            # Get Redis connection
            redis_conn = redis.Redis()

            # Test connection
            redis_conn.ping()
            self.stdout.write('Connected to Redis successfully')

            # Get all active rooms
            active_room_slugs = set(Room.objects.values_list('slug', flat=True))
            self.stdout.write(f'Found {len(active_room_slugs)} active rooms')

            # Find and clean room-specific presence sets
            cleaned_count = 0
            for pattern in ['room_*_online']:
                keys = redis_conn.keys(pattern)
                for key in keys:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    # Extract room slug from key format: room_{slug}_online
                    if key_str.startswith('room_') and key_str.endswith('_online'):
                        parts = key_str.split('_')
                        if len(parts) >= 3:
                            room_slug = '_'.join(parts[1:-1])  # Handle slugs with underscores
                            if room_slug not in active_room_slugs:
                                # Room no longer exists - clean up
                                redis_conn.delete(key)
                                cleaned_count += 1
                                self.stdout.write(f'Cleaned up stale presence set: {key_str}')

            # Clean global online users - remove users who are not active
            global_users = redis_conn.smembers('global_online_users')
            removed_count = 0
            for user_entry in global_users:
                user_id = int(user_entry.decode()) if isinstance(user_entry, bytes) else user_entry
                # Check if user exists and is active
                from accounts.models import User
                if not User.objects.filter(id=user_id, is_active=True).exists():
                    redis_conn.srem('global_online_users', user_id)
                    removed_count += 1
                    self.stdout.write(f'Removed inactive user from global presence: {user_id}')

            self.stdout.write(
                self.style.SUCCESS(
                    f'Cleanup complete! Removed {cleaned_count} stale room presence sets '
                    f'and {removed_count} inactive global users'
                )
            )

        except redis.RedisError as e:
            self.stderr.write(self.style.ERROR(f'Redis error: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Unexpected error: {e}'))
            logger.exception('Redis cleanup failed')
