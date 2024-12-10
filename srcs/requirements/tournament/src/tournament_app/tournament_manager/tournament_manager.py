from ..utils.logger import logger
from .data import game_modes_data
from ..tournament.tournament import Tournament
import uuid
import copy

class Tournament_manager:
	def __init__(self) :
		self.tournaments_room = {}
		self.status_list = [
			'waiting', 'startup', 'loading', 'running', 'aborted', 'finished'
		]
		logger.debug("\n\ntournament_manager initialised\n\n")

	def add_tournaments_room(self, tournament_id, admin_id, game_mode, modifiers, players_list, special_id):
		if (game_mode not in game_modes_data):
			logger.debug(f"Error: Wrong tournament_mode: {game_mode}")
			return None
		if len(players_list) != game_modes_data[game_mode]['players'] * 2:
			logger.debug(f"Error: Wrong nomber of players for the tournament mode {game_mode}: {len(players_list)}")
			return None
		self.tournaments_room[tournament_id] = {
			'status': 'waiting',
			'game_mode': game_mode,
			'modifiers': modifiers,
			'admin': {
				'id': admin_id,
				'consumer': None
			},
			'expected_players': players_list,
			'players': {},
			'spectator': {},
			'special_id': special_id,
			'tournament_instance': None
		}
		return self.tournaments_room[tournament_id]

	def special_connection(self, special_id, tournament_id):
		if tournament_id not in self.tournaments_room:
			return None
		room = self.tournaments_room[tournament_id]
		if not room['special_id']:
			return None
		for ids in room['special_id']:
			private_id = ids.get('private')
			if private_id == special_id:
				public_id = ids.get('public')
				if public_id:
					return public_id
				else:
					return None
		return None

	def add_user(self, username, nickname, consumer, tournament_id):
		if tournament_id not in self.tournaments_room:
			return None
		room = self.tournaments_room[tournament_id]
		if not room['admin']['consumer']:
			return None
		users = room['players']
		log_user = 'Player'
		if username not in room['expected_players']:
			users = room['spectator']
			log_user = 'Spectator'
		logger.debug(f"{log_user}: {username} is in waiting room !")
		users[username] = {
			'consumer': consumer,
			'nickname': nickname
		}
		logger.debug(f"players: {room['players']}")
		game_mode = room['game_mode']
		modifiers = room['modifiers']
		if room['status'] == 'waiting'\
			and len(room['players']) is game_modes_data[game_mode]['players'] * 2:
			logger.debug('player start the tournament')
			room['status'] = 'startup'
			players_test = room['players']#self.generatePlayers(16)
			logger.debug(f"players_test: {players_test}")
			new_tournament = Tournament(players_test, game_mode, modifiers)
			room['tournament_instance'] = new_tournament
		return room

	def generatePlayers(self, n):
		players_test = {}
		i = 1
		while i < n + 1:
			players_test[f"un_{str(i)}"] = {
				'consumer': None,
				'nickname': f"nn_{str(i)}"
			}
			i += 1
		return players_test

	def add_admin(self, admin_id, consumer, tournament_id):
		if tournament_id not in self.tournaments_room:
			return None
		room = self.tournaments_room[tournament_id]
		room_admin_id = room['admin']['id']
		if admin_id != room['admin']['id']:
			logger.debug('wrong admin_id')
			logger.debug(f'admin_id : {room_admin_id}')
			return None
		room['admin']['consumer'] = consumer
		game_mode = room['game_mode']
		if room['status'] == 'waiting'\
			and len(room['players']) is game_modes_data[game_mode]['players'] \
			and room['admin']['consumer']:
			logger.debug('admin start the tournament')
			room['status'] = 'startup'
			new_tournament = Tournament(room['players'])
			room['tournament_instance'] = new_tournament
		return room

	def update_status(self, status, tournament_id):
		if tournament_id not in self.tournaments_room \
			or status not in self.status_list:
			return None
		room = self.tournaments_room[tournament_id]
		room['status'] = status

	def remove_user(self, username, tournament_id):
		if tournament_id not in self.tournaments_room:
			return
		room = self.tournaments_room[tournament_id]
		users = room['players']
		if username not in room['expected_players']:
			users = room['spectator']
		if username in users:
			del users[username]

	def remove_room(self, tournament_id):
		if tournament_id in self.tournaments_room:
			del self.tournaments_room[tournament_id]

	def get_room(self, tournament_id):
		if tournament_id in self.tournaments_room:
			return self.tournaments_room[tournament_id]
		return None

	def aborttournament(self, tournament_id):
		if tournament_id in self.tournaments_room:
			self.tournaments_room[tournament_id]['status'] = 'aborted'
			return True
		else:
			return None

tournament_manager = Tournament_manager()
