


from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assistant'

    def ready(self):
        import assistant.signals  # Import signals here
