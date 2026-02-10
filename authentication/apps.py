from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    # DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
    name = 'authentication'

    def ready(self):
        # This imports the signals when the app is ready
        import authentication.signals 




# authentication/apps.py
# from django.apps import AppConfig

# class AuthenticationConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'authentication'

#     def ready(self):
#         # This imports the signals when the app is ready
#         import authentication.signals 
