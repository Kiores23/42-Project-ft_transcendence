from django.conf import settings
from .models import Player, GameInstance, PlayerGameHistory
from .utils.logger import logger
from .private_room.private_room import PrivateRoom, GenerateUsername
from admin_manager.admin_manager import AdminManager
from .utils.timer import Timer
from django.apps import apps
from django.db import connection
from asgiref.sync import sync_to_async
from django.db import transaction
import threading
import asyncio
import httpx
import uuid

class Game_manager:
	game_manager_instance = None

	def __init__(self):
		self.update_databases()
		self.private_rooms = {}
		self.username_generator = GenerateUsername()
		self._task = None
		self._is_running_mutex = threading.Lock()
		self._current_games = {}
		self._current_games_mutex = threading.Lock()
		self.status_timer = {
			'waiting': 20,
			'loading' : 60,
			'in_progress': 3600
		}

	def update_databases(self):
		if apps.is_installed('game_manager') and 'game_manager_player' in connection.introspection.table_names():
			players = Player.objects.all()
			if players:
				[player.update_status('inactive') for player in players if player.status!= 'inactive']
		if apps.is_installed('game_manager') and 'game_manager_gameinstance' in connection.introspection.table_names():
			games_instance = GameInstance.objects.all()
			if games_instance:
				for game_instance in games_instance:
					if game_instance.status != 'finished'\
						and  game_instance.status != 'aborted':
						game_instance.abort_game()

	def generate_username(self):
		logger.debug("generate new username")
		return self.username_generator.generate()

	def add_private_room(self, username):
		self.private_rooms[username] = PrivateRoom(username)
		return self.private_rooms[username]

	def add_new_game(self, game_id):
		game = GameInstance.get_game(game_id)
		if game.status and game.status not in ['finished', 'aborted']:
			with self._current_games_mutex:
				players_queryset = PlayerGameHistory.objects.filter(game=game)
				logger.debug(f"Raw PlayerGameHistory queryset for game {game_id}: {players_queryset}")
			
				players_list = list(players_queryset.values_list('player__username', flat=True))
				logger.debug(f"Player usernames for game {game_id}: {players_list}")
	
				self._current_games[game_id] = {
					'status': game.status,
					'latest_update_status': Timer(),
					'players': players_list
				}

	async def create_game(self, game_mode, modifiers, players_list, teams_list, ia_authorizes):
		# pars game_mode
		game_mode_data = settings.GAME_MODES.get(game_mode) 
		if game_mode_data is None:
			return None
		# pars modifiers
		modifiers_list = self.parse_modifier(modifiers, game_mode)
		if modifiers_list is None:
			return None
		# pars players_list
		if len(players_list) > game_mode_data['number_of_players']\
			or (ia_authorizes is False and len(players_list) < game_mode_data['number_of_players']):
			return None
		# pars teams_list
		if not teams_list:
			teams_list = []
		if game_mode_data['team_names'] is None\
			or len(teams_list) != len(game_mode_data['team_names']):
			return None
		number_of_players = 0
		for i, team_name in enumerate(game_mode_data['team_names']):
			if i >= len(teams_list):
				teams_list.append([])
		for team in teams_list:
			team_size = len(team)
			if team_size > game_mode_data['team_size']:
				return None
			number_of_players += team_size
		if number_of_players != len(players_list):
			return None
		if all(any(player in team for team in teams_list) for player in players_list) is False:
			return None
		# ai
		all_ai = []
		special_id = []
		while ia_authorizes and len(players_list) < game_mode_data['number_of_players']:
			ai_id = {
				'private': str(uuid.uuid4()),
				'public': str(uuid.uuid4())
			}
			all_ai.append(ai_id)
			special_id.append(ai_id)
			players_list.append(ai_id['public'])
			for team in teams_list:
				if len(team) < game_mode_data['team_size']:
					team.append(ai_id['public'])
					break
		game_id = str(uuid.uuid4())
		admin_id = str(uuid.uuid4())
		game = None
		game_connected = await self.connect_to_game(game_id, admin_id, game_mode, modifiers, players_list, special_id)
		if game_connected:
			game = await self.create_new_game_instance(game_id, game_mode, players_list)
			if not game:
				await self.disconnect_to_game(game_id, game_mode)
		else:
			return None
		ai_url = "http://ia:8000/api/ia/create_ia/"
		for ai_id in all_ai:
			try:
				ids = {
					'game_id': game_id,
					'ai_id': ai_id,
				}
				async with httpx.AsyncClient() as client:
					response = await client.post(ai_url, json=ids)  # Utilisation du paramètre json

				if response.status_code == 200:  # Succès explicite
					continue
				else:
					logger.error(f"Failed to create AI {ai_id}: {response.status_code} - {response.text}")
					return None
			except httpx.RequestError as e:
				logger.error(f"AI service error for AI {ai_id}: {str(e)}")
				#return None
		return {
			'game_id': game_id,
			'service_name': game_mode_data['service_name']
		}

	# game notify

	async def game_notify(self, game_id, admin_id, game_mode, modifiers, players, special_id=None):
		game_service_url = settings.GAME_MODES.get(game_mode).get('service_url_new_game')
		send = {'gameId': game_id, 'adminId': admin_id, 'gameMode': game_mode, 'playersList': players}
		logger.debug(f"send to {game_service_url}: {send}")
		try:
			async with httpx.AsyncClient() as client:
				response = await client.post(game_service_url, json={
					'gameId': game_id,
					'adminId': admin_id,
					'gameMode': game_mode,
					'modifiers': modifiers,
					'playersList': players,
					'special_id': special_id
				})
			if response and response.status_code == 201 :
				return True
			else:
				logger.debug(f'Error api request Game, response: {response}')
		except httpx.RequestError as e:
			logger.error(f"Authentication service error: {str(e)}")
		return False

	async def game_abort_notify(self, game_id, game_mode):
		game_service_url = settings.GAME_MODES.get(game_mode).get('service_url_abort_game')
		send = {'gameId': game_id}
		logger.debug(f"send to {game_service_url}: {send}")
		try:
			async with httpx.AsyncClient() as client:
				response = await client.post(game_service_url, json={
					'gameId': game_id
				})
			if response and response.status_code == 204 :
				return True
			else:
				logger.debug(f'Error api request Game, response: {response}')
		except httpx.RequestError as e:
			logger.error(f"Authentication service error: {str(e)}")
		return False

	# game connection

	async def connect_to_game(self, game_id, admin_id, game_mode, modifiers, players, special_id=None):
		is_game_notified = await Game_manager.game_manager_instance.game_notify(game_id, admin_id, game_mode, modifiers, players, special_id)
		if is_game_notified:
			logger.debug(f'Game service {game_id} created with players: {players}')
			AdminManager.admin_manager_instance.start_connections(game_id, admin_id, game_mode)
			return True
		else:
			return False

	async def disconnect_to_game(self, game_id, game_mode):
		is_game_notified = await Game_manager.game_manager_instance.game_abort_notify(game_id, game_mode)
		if is_game_notified:
			logger.debug(f'Game service {game_id} aborted')
			return True
		else:
			logger.debug(f'Game serice {game_id} was not aborted')
			return False

	# LOOP

	@sync_to_async	
	def _set_current_game_status(self, game_id):
		current_game = self._current_games[game_id]
		game_instance = GameInstance.get_game(game_id)
		if game_instance and game_instance.status\
			and game_instance.status != 'finished' and game_instance.status != 'aborted':
			if current_game['latest_update_status'].get_elapsed_time() \
				>= self.status_timer[current_game['status']]:
					if game_instance.status != self._current_games[game_id]['status']:
						logger.debug(f"{current_game['latest_update_status'].get_elapsed_time()}s elapsed with status : {self._current_games[game_id]['status']}")
						current_game['status'] = game_instance.status
						current_game['latest_update_status'].reset()
						return None, None
					else:
						logger.debug(f"{current_game['latest_update_status'].get_elapsed_time()}s abort game : {self._current_games[game_id]['status']}")
						for player in current_game['players']:
							player_instance = Player.get_player(player)
							if player_instance:
								player_instance.update_status('inactive')
						game_instance.abort_game()
						return game_id, game_instance.game_mode
			else :
				return None, None
		else:
			for player in current_game['players']:
				player_instance = Player.get_player(player)
				if player_instance:
					player_instance.update_status('inactive')
			return game_id, None

	async def _game_manager_logic(self):
		with self._current_games_mutex:
			for game_id in self._current_games:
				#logger.debug(f"{game_id} check status...")
				result = await self._set_current_game_status(game_id)
				if result:
					game_id, game_mode = result
					if game_mode:
						await self.game_abort_notify(game_id, game_mode)
					if game_id:
						del self._current_games[game_id]
						break

	async def _game_manager_loop(self):
		logger.debug("game_manager loop started")
		while True:
			with self._is_running_mutex:
				if not self._is_running:
					break
			#logger.debug("game_manager loop is running...")
			await self._game_manager_logic()
			await asyncio.sleep(1)

	async def start_game_manager_loop(self):
		with self._is_running_mutex:
			self._is_running = True
		self._task = asyncio.create_task(self._game_manager_loop())
		try:
			await self._task
		except asyncio.CancelledError:
			logger.debug("Game_manager loop has been cancelled.")
		finally:
			logger.debug("Exiting game_manager loop.")

	def stop_game_manager(self):
		logger.debug("Game_manager stopping...")
		with self._is_running_mutex:
			self._is_running = False
			if self._task:
				self._task.cancel()

	# db

	async def create_new_game_instance(self, game_id, game_mode, players):
		game = await self.create_game_instance(game_id, game_mode, players)
		if game:
			for username in players:
				await self.update_player_status(username, 'pending')
			return game
		else:
			return None
		
	async def create_new_player_instance(self, username):
		await self.create_player_instance(username)

	@sync_to_async
	def create_game_instance(self, game_id, game_mode, players):
		with transaction.atomic():
			game_instance = GameInstance.create_game(game_id, game_mode, players)
			Game_manager.game_manager_instance.add_new_game(game_id)
			return game_instance
		return None

	@sync_to_async
	def get_player_status(self, username):
		with transaction.atomic():
			player = Player.get_player(username)
			if player:
				return player.status
		return None

	@sync_to_async
	def update_player_status(self, username, status):
		with transaction.atomic():
			player = Player.get_player(username)
			if player:
				player.update_status(status)

	@sync_to_async
	def abord_game_instance(self, game):
		with transaction.atomic():
			game.abort_game()

	@sync_to_async
	def create_player_instance(self, username):
		with transaction.atomic():
			Player.get_or_create_player(username)

	#utils

	def parse_modifier(self, modifiers, game_mode):
		modifiers_list = modifiers.split(",") if modifiers else []
		valid_modifiers = settings.GAME_MODES.get(game_mode).get("modifier_list")
		if not all(mod in valid_modifiers for mod in modifiers_list):
			return None
		modifiers_list.sort()
		return modifiers_list

def create_game_manager_instance():
	if Game_manager.game_manager_instance is None:
		logger.debug("creating game manager...")
		Game_manager.game_manager_instance = Game_manager()
		logger.debug("game manager created !")