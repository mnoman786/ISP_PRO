"""
Unmanaged models mapping to FreeRADIUS MySQL tables.
Django will never run migrations on these — the tables are owned by FreeRADIUS.
"""
from django.db import models


class Radcheck(models.Model):
    """Per-user check attributes (password, Auth-Type=Reject for disabled users)."""
    username = models.CharField(max_length=64)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default=':=')
    value = models.CharField(max_length=253)

    class Meta:
        app_label = 'radius'
        db_table = 'radcheck'
        managed = False

    def __str__(self):
        return f"{self.username} | {self.attribute} {self.op} {self.value}"


class Radreply(models.Model):
    """Per-user reply attributes (Framed-IP-Address for static IP etc.)."""
    username = models.CharField(max_length=64)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default=':=')
    value = models.CharField(max_length=253)

    class Meta:
        app_label = 'radius'
        db_table = 'radreply'
        managed = False

    def __str__(self):
        return f"{self.username} | {self.attribute} {self.op} {self.value}"


class RadUserGroup(models.Model):
    """Maps a username to a group (package profile)."""
    username = models.CharField(max_length=64)
    groupname = models.CharField(max_length=64)
    priority = models.IntegerField(default=0)

    class Meta:
        app_label = 'radius'
        db_table = 'radusergroup'
        managed = False

    def __str__(self):
        return f"{self.username} → {self.groupname}"


class RadGroupReply(models.Model):
    """Group-level reply attributes — bandwidth limits per package group."""
    groupname = models.CharField(max_length=64)
    attribute = models.CharField(max_length=64)
    op = models.CharField(max_length=2, default=':=')
    value = models.CharField(max_length=253)

    class Meta:
        app_label = 'radius'
        db_table = 'radgroupreply'
        managed = False

    def __str__(self):
        return f"[{self.groupname}] {self.attribute} {self.op} {self.value}"


class Radacct(models.Model):
    """Accounting records written by FreeRADIUS — read-only from the CRM."""
    radacctid = models.BigAutoField(primary_key=True)
    acctsessionid = models.CharField(max_length=64)
    acctuniqueid = models.CharField(max_length=32, unique=True)
    username = models.CharField(max_length=64)
    realm = models.CharField(max_length=64, blank=True)
    nasipaddress = models.CharField(max_length=15)
    nasportid = models.CharField(max_length=32, blank=True)
    nasporttype = models.CharField(max_length=32, blank=True)
    acctstarttime = models.DateTimeField(null=True)
    acctupdatetime = models.DateTimeField(null=True)
    acctstoptime = models.DateTimeField(null=True)
    acctsessiontime = models.IntegerField(null=True)
    acctinputoctets = models.BigIntegerField(null=True)
    acctoutputoctets = models.BigIntegerField(null=True)
    calledstationid = models.CharField(max_length=50, blank=True)
    callingstationid = models.CharField(max_length=50, blank=True)
    acctterminatecause = models.CharField(max_length=32, blank=True)
    framedipaddress = models.CharField(max_length=15, blank=True)

    class Meta:
        app_label = 'radius'
        db_table = 'radacct'
        managed = False
        ordering = ['-acctstarttime']

    def __str__(self):
        return f"{self.username} @ {self.acctstarttime}"

    @property
    def rx_mb(self):
        return round((self.acctinputoctets or 0) / 1048576, 2)

    @property
    def tx_mb(self):
        return round((self.acctoutputoctets or 0) / 1048576, 2)
