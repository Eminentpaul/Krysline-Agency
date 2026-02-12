from django.apps import AppConfig
# import s


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'


    def ready(self):
        import users.signals  # This line activates the signals
