from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        # importa aquí tu módulo de señales
        import core.signals
