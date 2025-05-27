class AuthRouter:
    route_app_labels = {'auth', 'contenttypes', 'sessions', 'admin', 'members'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'auth_db'
        return 'eisphora_db'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'auth_db'
        return 'eisphora_db'

    def allow_relation(self, obj1, obj2, **hints):
        db_obj1 = self.db_for_read(obj1)
        db_obj2 = self.db_for_read(obj2)
        if db_obj1 and db_obj2:
            return db_obj1 == db_obj2
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == 'auth_db'
        return db == 'eisphora_db'
