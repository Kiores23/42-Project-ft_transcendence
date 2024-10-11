from django.apps import AppConfig
from game_manager.utils.logger import logger

class MatchmakingConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'matchmaking'
	def ready(self):
		from django.core.signals import request_started
		from django.dispatch import receiver
		from .thread import start_matchmaking, stop_matchmaking
		from game_manager.utils.logger import logger
		import atexit
		
		@receiver(request_started)
		def start(sender, **kwargs):
			logger.debug("starting matchmaking...")
			start_matchmaking()
			atexit.register(stop_matchmaking)
