class RadiusRouter:
    """Route all radius app models to the 'radius' database. Never migrate."""
    app_label = 'radius'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'radius'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'radius'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, **hints):
        if app_label == self.app_label:
            return False
        return None
