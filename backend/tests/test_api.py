import unittest
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from app.models.game import Game
from app.models.player import Player


class TestAuthAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_register(self):
        resp = self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
        })

        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn('access_token', data)
        self.assertEqual(data['user']['username'], 'testuser')

    def test_register_missing_fields(self):
        resp = self.client.post('/api/auth/register', json={
            'username': 'testuser',
        })
        self.assertEqual(resp.status_code, 400)

    def test_register_duplicate_username(self):
        self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test1@example.com',
            'password': 'password123',
        })
        resp = self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test2@example.com',
            'password': 'password123',
        })
        self.assertEqual(resp.status_code, 409)

    def test_login(self):
        self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
        })
        resp = self.client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123',
        })

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('access_token', data)

    def test_login_wrong_password(self):
        self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
        })
        resp = self.client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(resp.status_code, 401)

    def test_get_profile(self):
        reg = self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
        })
        token = reg.get_json()['access_token']

        resp = self.client.get('/api/auth/profile', headers={
            'Authorization': f'Bearer {token}',
        })

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['username'], 'testuser')

    def test_get_profile_unauthorized(self):
        resp = self.client.get('/api/auth/profile')
        self.assertEqual(resp.status_code, 401)


class TestGamesAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.player_w = Player(name='WhitePlayer')
        self.player_b = Player(name='BlackPlayer')
        db.session.add_all([self.player_w, self.player_b])
        db.session.commit()

        self.game = Game(
            white_player_id=self.player_w.id,
            black_player_id=self.player_b.id,
            result='1-0',
            eco_code='C42',
            opening_name="Petrov's Defense",
            pgn_content='1. e4 e5 2. Nf3 Nf6 1-0',
            total_moves=2,
        )
        db.session.add(self.game)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_get_games(self):
        resp = self.client.get('/api/games')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('items', data)
        self.assertEqual(data['total'], 1)

    def test_get_game_detail(self):
        resp = self.client.get(f'/api/games/{self.game.id}')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['eco_code'], 'C42')

    def test_get_game_not_found(self):
        resp = self.client.get('/api/games/9999')
        self.assertEqual(resp.status_code, 404)

    def test_get_games_with_search(self):
        resp = self.client.get('/api/games?search=WhitePlayer')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['total'], 1)

    def test_get_games_with_eco_filter(self):
        resp = self.client.get('/api/games?eco=C42')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['total'], 1)

    def test_get_games_with_result_filter(self):
        resp = self.client.get('/api/games?result=0-1')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['total'], 0)


class TestPlayersAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.player = Player(name='Magnus', elo_rating=2860)
        db.session.add(self.player)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_get_players(self):
        resp = self.client.get('/api/players')
        self.assertEqual(resp.status_code, 200)

    def test_get_player_detail(self):
        resp = self.client.get(f'/api/players/{self.player.id}')
        self.assertEqual(resp.status_code, 200)

    def test_get_player_not_found(self):
        resp = self.client.get('/api/players/9999')
        self.assertEqual(resp.status_code, 404)


if __name__ == '__main__':
    unittest.main()
