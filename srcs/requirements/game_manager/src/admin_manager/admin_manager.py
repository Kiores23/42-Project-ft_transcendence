import threading
import websockets
import asyncio
from game_manager.models import GameInstance, Player
from django.db import transaction
from django.conf import settings
from game_manager.utils.logger import logger
from asgiref.sync import sync_to_async
import json

class AdminManager:
	admin_manager_instance = None

	def __init__(self):
		self.threads = {}

	def connect_to_game(self, game_id, admin_id, ws_url):
		# Démarre un nouvel event loop pour chaque thread
		logger.debug(f'new thread created to {ws_url} !')
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		try:
			loop.run_until_complete(self._handle_websocket(game_id, ws_url))
		finally:
	   		self.cleanup_thread(game_id)

	def cleanup_thread(self, game_id):
		users = self.threads[game_id]['users']
		logger.debug(f"Cleanup after game {game_id}. Closing resources...")
		logger.debug(f"users change status : {users}")
		self.upadte_game_status(game_id, users, 'aborted')
		del self.threads[game_id]
		logger.debug(f"Thread for game {game_id} cleaned up.")
	
	async def _handle_websocket(self, game_id, ws_url):
		users = self.threads[game_id]['users']
		logger.debug(f'thread in game : {game_id} is running...')
		async with websockets.connect(ws_url) as websocket:
			logger.debug(f"Websocket connected : {ws_url}")
			try:
				async for message in websocket:
					message_dict = json.loads(message)
					await self.handle_message(game_id, message_dict, users)
			except websockets.exceptions.ConnectionClosedOK:
				logger.debug("WebSocket connection closed normally (1000 OK).")
			except websockets.exceptions.ConnectionClosedError as e:
				logger.error(f"WebSocket closed with error: {e}")
			except json.JSONDecodeError as e:
				logger.error(f"Failed to decode message: {e}")

	@sync_to_async
	def handle_message(self, game_id, message, users):
		logger.debug(f"Game {game_id}: Received message: {message}")
		type = message.get("type")
		if type == "export_status":
			status = message.get("status")
			if status == "finished":
				win_team = message.get("team")
				score = message.get("score")
				self.set_winner(game_id, win_team, score)
			self.upadte_game_status(game_id, users, status)
		elif type == "export_teams":
			teams = message.get("teams")
			self.export_teams(game_id, teams)
		elif type == "update_score":
			team = message.get("team")
			score = message.get("score")
			self.update_score(game_id, team, score)
		elif type == "player_connection":
			username = message.get("username")
			users['players'].append(username)
			self.update_user_status(username, 'waiting_for_players')
		elif type == "spectator_connection":
			username = message.get("username")
			users['spectators'].append(username)
			self.update_user_status(username, 'spectate')
		elif type == "player_disconnection":
			username = message.get("username")
			self.update_user_status(username, 'inactive')
			users['players'].remove(username)
		elif type == "spectator_disconnection":
			username = message.get("username")
			self.update_user_status(username, 'inactive')
			users['spectators'].remove(username)

	def set_winner(self, game_id, win_team, score):
		game_instance = GameInstance.get_game(game_id)
		if not game_instance:
			logger.debug("game instance is None")
			return
		with transaction.atomic():
			game_instance.update_score(win_team, score)
			game_instance.set_winner(win_team)

	def upadte_game_status(self, game_id, users, status):
		self.update_users_status_with_game_status(users, status)
		game_instance = GameInstance.get_game(game_id)
		if not game_instance:
			logger.debug("game instance is None")
			return
		if game_instance.status == 'finished' \
			or game_instance.status == 'aborted':
			return
		with transaction.atomic():
			game_instance.update_status(status)

	def update_users_status_with_game_status(self, users, game_status):
		if game_status == 'loading':
			self.change_all_players_status(users, 'loading_game')
		if game_status == 'in_progress':
			self.change_all_players_status(users, 'in_game')
		if game_status == 'aborted' or game_status == 'finished':
			self.change_all_players_status(users, 'inactive')
			self.change_all_spectators_status(users, 'inactive')

	def export_teams(self, game_id, teams):
		game_instance = GameInstance.get_game(game_id)
		if not game_instance:
			return
		with transaction.atomic():
			for team in teams:
				for player in teams[team]:
					game_instance.add_player_to_team(player, team)

	def update_score(self, game_id, team, score):
		game_instance = GameInstance.get_game(game_id)
		if not game_instance:
			return
		with transaction.atomic():
			game_instance.update_score(team, score)

	def change_all_players_status(self, users, status):
		for username in users['players']:
			self.update_user_status(username, status)
		if status == 'inactive':
			for username in users['players']:
				users['players'].remove(username)
		
	def change_all_spectators_status(self, users, status):
		for username in users['spectators']:
			self.update_user_status(username, status)
		if status == 'inactive':
			for username in users['spectators']:
				users['spectators'].remove(username)

	def update_user_status(self, username, status):
		with transaction.atomic():
			player = Player.get_or_create_player(username)
			if player:
				player.update_status(status)		

	# ADMIN_MANAGER

	def start_connections(self, game_id, admin_id, game_mode):
		# Extraire les informations de la partie
		ws_url = settings.GAME_MODES.get(game_mode).get('service_ws') + game_id + '/' + admin_id + '/'
		logger.debug(f'start_new_connection ws - game_id = {game_id}, admin_id = {admin_id}, ws_url = {ws_url}')
		# Créer un thread pour la connexion WebSocket
		thread = threading.Thread(target=self.connect_to_game, args=(game_id, admin_id, ws_url))
		thread.start()

		# Ajouter le thread à la liste des threads
		self.threads[game_id] = {
			'thread': thread,
			'users': {
				'players': [],
				'spectators': []
			}
		}

	def close(self, game_id):
		threads[game_id]['thread'].stop()

	def close_all(self):
		for game_id in self.threads:
			threads[game_id]['thread'].join()
		logger.debug("Tous les threads sont terminés, fermeture du programme.")

if AdminManager.admin_manager_instance is None:
	AdminManager.admin_manager_instance = AdminManager()
