"""
FreeRADIUS service — manages users in radcheck/radreply/radusergroup/radgroupreply.

All public functions return (success: bool, message: str).
When RADIUS_ENABLED=False every function is a safe no-op.
"""
from django.conf import settings


def is_enabled():
    return getattr(settings, 'RADIUS_ENABLED', False)


def _noop(msg='RADIUS not enabled — skipped'):
    return True, msg


def push_user(connection):
    """
    Create or fully replace a user's RADIUS entries.
    - Active   → Cleartext-Password + optional Framed-IP-Address + group membership
    - Anything else → Auth-Type=Reject (blocks auth without deleting the record)
    """
    if not is_enabled():
        return _noop()
    from .models import Radcheck, Radreply, RadUserGroup
    try:
        username = connection.username

        # Wipe existing entries so we start clean
        Radcheck.objects.using('radius').filter(username=username).delete()
        Radreply.objects.using('radius').filter(username=username).delete()
        RadUserGroup.objects.using('radius').filter(username=username).delete()

        if connection.status == 'active':
            Radcheck.objects.using('radius').create(
                username=username, attribute='Cleartext-Password',
                op=':=', value=connection.password,
            )
            if connection.ip_address and connection.static_ip:
                Radreply.objects.using('radius').create(
                    username=username, attribute='Framed-IP-Address',
                    op=':=', value=str(connection.ip_address),
                )
            if connection.package:
                RadUserGroup.objects.using('radius').create(
                    username=username, groupname=connection.package.name, priority=0,
                )
            return True, f"RADIUS: user '{username}' pushed (active)"
        else:
            # Reject auth — user sees "access denied" on the router
            Radcheck.objects.using('radius').create(
                username=username, attribute='Auth-Type', op=':=', value='Reject',
            )
            return True, f"RADIUS: user '{username}' set to Reject"
    except Exception as e:
        return False, f"RADIUS error: {e}"


def disable_user(username):
    """Block a user by replacing their password entry with Auth-Type=Reject."""
    if not is_enabled():
        return _noop()
    from .models import Radcheck, Radreply, RadUserGroup
    try:
        Radcheck.objects.using('radius').filter(username=username).delete()
        Radreply.objects.using('radius').filter(username=username).delete()
        RadUserGroup.objects.using('radius').filter(username=username).delete()
        Radcheck.objects.using('radius').create(
            username=username, attribute='Auth-Type', op=':=', value='Reject',
        )
        return True, f"RADIUS: disabled '{username}'"
    except Exception as e:
        return False, f"RADIUS error: {e}"


def enable_user(connection):
    """Re-enable by pushing the full connection (clears Reject, sets password + group)."""
    return push_user(connection)


def delete_user(username):
    """Remove all RADIUS entries for a user (use when deleting a connection)."""
    if not is_enabled():
        return _noop()
    from .models import Radcheck, Radreply, RadUserGroup
    try:
        Radcheck.objects.using('radius').filter(username=username).delete()
        Radreply.objects.using('radius').filter(username=username).delete()
        RadUserGroup.objects.using('radius').filter(username=username).delete()
        return True, f"RADIUS: deleted '{username}'"
    except Exception as e:
        return False, f"RADIUS error: {e}"


def sync_package(package):
    """
    Push a package as a FreeRADIUS group with Mikrotik-Rate-Limit.
    Call this whenever a package is created or its speeds change.
    MikroTik reads this attribute from RADIUS reply and applies the queue.
    """
    if not is_enabled():
        return _noop()
    from .models import RadGroupReply
    try:
        groupname = package.name
        RadGroupReply.objects.using('radius').filter(
            groupname=groupname, attribute='Mikrotik-Rate-Limit',
        ).delete()
        dl = package.speed_download or 0
        ul = package.speed_upload or 0
        if dl or ul:
            RadGroupReply.objects.using('radius').create(
                groupname=groupname, attribute='Mikrotik-Rate-Limit',
                op=':=', value=f"{dl}M/{ul}M",
            )
        return True, f"RADIUS: package group '{groupname}' → {dl}M/{ul}M"
    except Exception as e:
        return False, f"RADIUS error: {e}"


def get_user_sessions(username, limit=20):
    """Return recent accounting records for a username (read from radacct)."""
    if not is_enabled():
        return []
    from .models import Radacct
    try:
        return list(
            Radacct.objects.using('radius')
            .filter(username=username)
            .order_by('-acctstarttime')[:limit]
        )
    except Exception:
        return []
