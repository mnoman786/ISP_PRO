"""
MikroTik API service — wraps routeros_api for PPPoE secret management.

All public functions return (success: bool, message: str).
"""
import routeros_api


def _connect(device):
    """Open a RouterOS API connection to a NetworkDevice."""
    pool = routeros_api.RouterOsApiPool(
        host=device.get_api_host(),
        port=device.api_port,
        username=device.api_username,
        password=device.api_password,
        use_ssl=device.api_use_ssl,
        ssl_verify=False,
        plaintext_login=True,  # required for RouterOS v6.49+
    )
    return pool.get_api()


def test_connection(device):
    """Test whether the API credentials work."""
    try:
        api = _connect(device)
        identity = api.get_resource('/system/identity').get()
        name = identity[0].get('name', 'MikroTik') if identity else 'MikroTik'
        api.disconnect()
        return True, f"Connected — router name: {name}"
    except Exception as e:
        return False, str(e)


def _get_secret(api, username):
    """Return the PPPoE secret dict for a username, or None."""
    secrets = api.get_resource('/ppp/secret').get(name=username)
    return secrets[0] if secrets else None


def push_pppoe_user(device, connection):
    """
    Create or update a PPPoE secret on MikroTik.
    Sets profile from the package name (must match a MikroTik profile).
    """
    try:
        api = _connect(device)
        resource = api.get_resource('/ppp/secret')
        existing = _get_secret(api, connection.username)

        profile = connection.package.name if connection.package else 'default'
        ip = str(connection.ip_address) if connection.ip_address and connection.static_ip else ''

        params = {
            'name': connection.username,
            'password': connection.password,
            'service': 'pppoe',
            'profile': profile,
            'disabled': 'no' if connection.status == 'active' else 'yes',
        }
        if ip:
            params['remote-address'] = ip
        if connection.olt_port:
            params['comment'] = connection.olt_port

        if existing:
            resource.call('set', dict(params, **{'.id': existing['.id']}))
            msg = f"Updated PPPoE secret for {connection.username}"
        else:
            resource.add(**params)
            msg = f"Created PPPoE secret for {connection.username}"

        api.disconnect()
        return True, msg
    except Exception as e:
        return False, str(e)


def enable_pppoe_user(device, username):
    """Enable (un-disable) a PPPoE secret."""
    try:
        api = _connect(device)
        secret = _get_secret(api, username)
        if not secret:
            api.disconnect()
            return False, f"PPPoE user '{username}' not found on router"
        api.get_resource('/ppp/secret').call('set', {'.id': secret['.id'], 'disabled': 'no'})
        # Also kick any active session so user reconnects with fresh auth
        _kick_active_session(api, username)
        api.disconnect()
        return True, f"Enabled PPPoE user: {username}"
    except Exception as e:
        return False, str(e)


def disable_pppoe_user(device, username):
    """Disable a PPPoE secret and drop the active session."""
    try:
        api = _connect(device)
        secret = _get_secret(api, username)
        if not secret:
            api.disconnect()
            return False, f"PPPoE user '{username}' not found on router"
        api.get_resource('/ppp/secret').call('set', {'.id': secret['.id'], 'disabled': 'yes'})
        _kick_active_session(api, username)
        api.disconnect()
        return True, f"Disabled PPPoE user: {username}"
    except Exception as e:
        return False, str(e)


def delete_pppoe_user(device, username):
    """Remove a PPPoE secret entirely."""
    try:
        api = _connect(device)
        secret = _get_secret(api, username)
        if not secret:
            api.disconnect()
            return True, f"User '{username}' did not exist on router"
        _kick_active_session(api, username)
        api.get_resource('/ppp/secret').call('remove', {'.id': secret['.id']})
        api.disconnect()
        return True, f"Deleted PPPoE user: {username}"
    except Exception as e:
        return False, str(e)


def _kick_active_session(api, username):
    """Terminate active PPPoE session for a user (best-effort, no exception raised)."""
    try:
        active = api.get_resource('/ppp/active').get(name=username)
        if active:
            api.get_resource('/ppp/active').call('remove', {'.id': active[0]['.id']})
    except Exception:
        pass


def get_active_sessions(device):
    """Return list of currently active PPPoE sessions from the router."""
    try:
        api = _connect(device)
        sessions = api.get_resource('/ppp/active').get()
        api.disconnect()
        return True, sessions
    except Exception as e:
        return False, str(e)


def sync_connection(connection):
    """
    High-level helper: push connection state to its linked MikroTik router.
    Safe to call even if no router is linked (returns True silently).
    """
    if not connection.mikrotik_router or not connection.mikrotik_router.is_mikrotik:
        return True, 'No MikroTik router linked — skipped'
    return push_pppoe_user(connection.mikrotik_router, connection)
