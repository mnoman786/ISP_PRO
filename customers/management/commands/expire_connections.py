from django.core.management.base import BaseCommand
from django.utils import timezone
from customers.models import Connection
from network.mikrotik import disable_pppoe_user
from radius import service as radius


class Command(BaseCommand):
    help = 'Expire connections whose expiry_date has passed and disable them on MikroTik + RADIUS.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be expired without making changes.',
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        dry_run = options['dry_run']

        expired = Connection.objects.filter(
            status=Connection.STATUS_ACTIVE,
            expiry_date__lt=today,
        ).select_related('mikrotik_router', 'customer')

        count = expired.count()
        if count == 0:
            self.stdout.write('No connections to expire.')
            return

        self.stdout.write(f'Found {count} connection(s) to expire.')

        for conn in expired:
            label = f'{conn.username} ({conn.customer.name})'
            if dry_run:
                self.stdout.write(f'  [dry-run] would expire: {label}')
                continue

            # Disable on MikroTik
            if conn.mikrotik_router and conn.mikrotik_router.is_mikrotik:
                ok, msg = disable_pppoe_user(conn.mikrotik_router, conn.username)
                if ok:
                    self.stdout.write(self.style.SUCCESS(f'  MikroTik disabled: {label}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  MikroTik error ({label}): {msg}'))

            # Disable in RADIUS
            r_ok, r_msg = radius.disable_user(conn.username)
            if r_ok and radius.is_enabled():
                self.stdout.write(self.style.SUCCESS(f'  RADIUS disabled: {label}'))
            elif not r_ok:
                self.stdout.write(self.style.WARNING(f'  RADIUS error ({label}): {r_msg}'))

            conn.status = Connection.STATUS_EXPIRED
            conn.save(update_fields=['status', 'updated_at'])
            self.stdout.write(self.style.SUCCESS(f'  Expired: {label}'))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Done — {count} connection(s) expired.'))
