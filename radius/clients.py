"""
Manages FreeRADIUS clients.conf entries for MikroTik devices.
Each CRM-managed client is tagged with # CRM:<device_pk> for easy find/replace/remove.
"""
import re
import subprocess
from django.conf import settings


def _conf_path():
    return getattr(settings, 'RADIUS_CLIENTS_CONF', '/etc/freeradius/3.0/clients.conf')


def _default_secret():
    return getattr(settings, 'RADIUS_DEFAULT_SECRET', 'testing123')


def _slug(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())


def _client_block(device):
    ip = device.get_api_host() or str(device.ip_address or '')
    secret = device.radius_secret.strip() or _default_secret()
    slug = _slug(device.name)
    return (
        f"\n# CRM:{device.pk}\n"
        f"client {slug} {{\n"
        f"    ipaddr    = {ip}\n"
        f"    secret    = {secret}\n"
        f"    shortname = {slug}\n"
        f"    nastype   = other\n"
        f"}}\n"
    )


def _remove_existing(content, device_pk):
    pattern = rf'\n# CRM:{device_pk}\nclient [^\{{]+\{{[^\}}]*\}}\n'
    return re.sub(pattern, '', content, flags=re.DOTALL)


def _reload_freeradius():
    try:
        subprocess.run(
            ['systemctl', 'reload', 'freeradius'],
            check=True, timeout=10,
            capture_output=True,
        )
        return True, 'FreeRADIUS reloaded'
    except Exception as e:
        return False, f'FreeRADIUS reload failed: {e}'


def add_or_update_client(device):
    """Write/update a client block for a MikroTik device and reload FreeRADIUS."""
    if not getattr(settings, 'RADIUS_ENABLED', False):
        return True, 'RADIUS not enabled — skipped'
    if not device.is_mikrotik:
        return True, 'Not a MikroTik device — skipped'
    ip = device.get_api_host() or str(device.ip_address or '')
    if not ip:
        return False, 'Device has no IP address set'
    try:
        content = open(_conf_path()).read()
        content = _remove_existing(content, device.pk)
        content += _client_block(device)
        open(_conf_path(), 'w').write(content)
        return _reload_freeradius()
    except Exception as e:
        return False, str(e)


def remove_client(device):
    """Remove a device's client block from clients.conf and reload FreeRADIUS."""
    if not getattr(settings, 'RADIUS_ENABLED', False):
        return True, 'RADIUS not enabled — skipped'
    try:
        content = open(_conf_path()).read()
        content = _remove_existing(content, device.pk)
        open(_conf_path(), 'w').write(content)
        return _reload_freeradius()
    except Exception as e:
        return False, str(e)
