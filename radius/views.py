from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings


@login_required
def sessions_list(request):
    """All currently online users from radacct."""
    enabled = getattr(settings, 'RADIUS_ENABLED', False)
    sessions = []
    total_rx = 0
    total_tx = 0

    if enabled:
        from .models import Radacct
        sessions = list(
            Radacct.objects.using('radius')
            .filter(acctstoptime__isnull=True)
            .order_by('-acctstarttime')
        )
        total_rx = sum((s.acctinputoctets or 0) for s in sessions)
        total_tx = sum((s.acctoutputoctets or 0) for s in sessions)

    return render(request, 'radius/sessions.html', {
        'sessions': sessions,
        'online_count': len(sessions),
        'total_rx_mb': round(total_rx / 1048576, 1),
        'total_tx_mb': round(total_tx / 1048576, 1),
        'radius_enabled': enabled,
    })


@login_required
def user_sessions(request, username):
    """Session history for a single PPPoE username."""
    enabled = getattr(settings, 'RADIUS_ENABLED', False)
    sessions = []
    if enabled:
        from .models import Radacct
        sessions = list(
            Radacct.objects.using('radius')
            .filter(username=username)
            .order_by('-acctstarttime')[:50]
        )
    return render(request, 'radius/user_sessions.html', {
        'sessions': sessions,
        'username': username,
        'radius_enabled': enabled,
    })
