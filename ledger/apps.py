# from django.apps import AppConfig


# class LedgerConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'ledger'




from django.apps import AppConfig

class LedgerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ledger'

    def ready(self):
        import ledger.signals # <--- This is the magic line



