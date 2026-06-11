import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import chess
from unittest.mock import patch, MagicMock

from app.services.ai_player import AIPlayer, PracticeSession, DIFFICULTY_CONFIG, PracticeError


class TestDifficultyConfig(unittest.TestCase):
    def test_all_difficulties_exist(self):
        for key in ['beginner', 'easy', 'medium', 'hard', 'expert']:
            self.assertIn(key, DIFFICULTY_CONFIG)
            cfg = DIFFICULTY_CONFIG[key]
            self.assertIn('depth', cfg)
            self.assertIn('random_rate', cfg)
            self.assertIn('blunder_rate', cfg)
            self.assertIn('label', cfg)

    def test_difficulty_ordering(self):
        depths = [DIFFICULTY_CONFIG[k]['depth'] for k in ['beginner', 'easy', 'medium', 'hard', 'expert']]
        self.assertEqual(depths, sorted(depths))

    def test_rates_sum_less_than_one(self):
        for key, cfg in DIFFICULTY_CONFIG.items():
            self.assertLessEqual(cfg['random_rate'] + cfg['blunder_rate'], 1.0,
                                 f'{key}: random_rate + blunder_rate > 1.0')


class TestAIPlayerMock(unittest.TestCase):
    def setUp(self):
        self.ai = AIPlayer.__new__(AIPlayer)
        self.ai.stockfish_path = 'stockfish'
        self.ai.difficulty = 'medium'
        self.ai.config = DIFFICULTY_CONFIG['medium']
        self.ai.engine = None
        self.ai._is_mock = True

    def test_get_move_returns_legal(self):
        board = chess.Board()
        move = self.ai.get_move(board)
        self.assertIsNotNone(move)
        self.assertIn(move, board.legal_moves)

    def test_get_move_no_legal_moves(self):
        board = chess.Board('rnb1kbnr/pppp1ppp/4p3/8/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3')
        move = self.ai.get_move(board)
        self.assertIsNone(move)

    def test_get_hint_returns_dict(self):
        board = chess.Board()
        hint = self.ai.get_hint(board)
        self.assertIn('hint_move', hint)
        self.assertIn('score', hint)
        self.assertIn('win_rate', hint)

    def test_close_no_error(self):
        self.ai.close()


class TestAIPlayerMoveSelection(unittest.TestCase):
    def setUp(self):
        self.ai = AIPlayer.__new__(AIPlayer)
        self.ai.stockfish_path = 'stockfish'
        self.ai.difficulty = 'medium'
        self.ai.config = DIFFICULTY_CONFIG['medium']
        self.ai.engine = None
        self.ai._is_mock = False

    def test_blunder_rate_selects_third_candidate(self):
        board = chess.Board()
        move1 = chess.Move.from_uci('e2e4')
        move2 = chess.Move.from_uci('d2d4')
        move3 = chess.Move.from_uci('g1f3')

        mock_info = [
            {'pv': [move1]},
            {'pv': [move2]},
            {'pv': [move3]},
        ]

        self.ai.engine = MagicMock()
        self.ai.engine.analyse.return_value = mock_info

        with patch('random.random', return_value=0.01):
            result = self.ai.get_move(board)
            self.assertEqual(result, move3)

    def test_random_rate_selects_second_candidate(self):
        board = chess.Board()
        move1 = chess.Move.from_uci('e2e4')
        move2 = chess.Move.from_uci('d2d4')
        move3 = chess.Move.from_uci('g1f3')

        mock_info = [
            {'pv': [move1]},
            {'pv': [move2]},
            {'pv': [move3]},
        ]

        self.ai.engine = MagicMock()
        self.ai.engine.analyse.return_value = mock_info

        with patch('random.random', return_value=0.05):
            result = self.ai.get_move(board)
            self.assertEqual(result, move2)

    def test_best_move_selected_normally(self):
        board = chess.Board()
        move1 = chess.Move.from_uci('e2e4')
        move2 = chess.Move.from_uci('d2d4')
        move3 = chess.Move.from_uci('g1f3')

        mock_info = [
            {'pv': [move1]},
            {'pv': [move2]},
            {'pv': [move3]},
        ]

        self.ai.engine = MagicMock()
        self.ai.engine.analyse.return_value = mock_info

        with patch('random.random', return_value=0.5):
            result = self.ai.get_move(board)
            self.assertEqual(result, move1)

    def test_fewer_candidates(self):
        board = chess.Board()
        move1 = chess.Move.from_uci('e2e4')

        mock_info = [{'pv': [move1]}]

        self.ai.engine = MagicMock()
        self.ai.engine.analyse.return_value = mock_info

        with patch('random.random', return_value=0.01):
            result = self.ai.get_move(board)
            self.assertEqual(result, move1)


class TestPracticeSessionBasic(unittest.TestCase):
    def setUp(self):
        self.session = PracticeSession.__new__(PracticeSession)
        self.session.stockfish_path = 'stockfish'
        self.session.engine = None
        self.session.board = None
        self.session.user_color = None
        self.session.history = []
        self.session.ai_player = None
        self.session.difficulty = 'medium'
        self.session.hints_used = 0
        self.session.undo_count = 0
        self.session._start_fen = None
        self.session._game_over = False
        self.session._result = None
        self.session._source = None
        self.session._source_id = None

    def test_start_from_fen_white(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            result = self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            self.assertEqual(result['user_color'] if 'user_color' in result else self.session.user_color, 'white')
            self.assertTrue(result['is_user_turn'])
            self.assertEqual(result['turn'], 'white')

    def test_start_from_fen_black_ai_moves_first(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()
        ai_move = chess.Move.from_uci('e2e4')
        mock_ai.get_move.return_value = ai_move

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai) as MockAI:
            result = self.session.start_from_fen(initial_fen, user_color='black', difficulty='easy')
            self.assertTrue(result['is_user_turn'])
            self.assertEqual(len(self.session.history), 1)
            self.assertEqual(self.session.history[0]['color'], 'ai')
            MockAI.assert_called_once_with('stockfish', 'easy')

    def test_user_move_normal(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()
        ai_move = chess.Move.from_uci('e7e5')
        mock_ai.get_move.return_value = ai_move

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            result = self.session.user_move('e4')
            self.assertIsNotNone(result['ai_move'])
            self.assertEqual(result['ai_move_san'], 'e5')
            self.assertFalse(result['is_game_over'])
            self.assertEqual(len(self.session.history), 2)
            self.assertEqual(self.session.history[0]['color'], 'user')
            self.assertEqual(self.session.history[1]['color'], 'ai')

    def test_user_move_invalid(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            with self.assertRaises(PracticeError):
                self.session.user_move('Qh5')

    def test_undo_two_moves(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()
        ai_move = chess.Move.from_uci('e7e5')
        mock_ai.get_move.return_value = ai_move

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            self.session.user_move('e4')
            self.assertEqual(len(self.session.history), 2)

            result = self.session.undo_move()
            self.assertEqual(len(self.session.history), 0)
            self.assertTrue(result['is_user_turn'])
            self.assertEqual(self.session.board.fen(), initial_fen)
            self.assertEqual(self.session.undo_count, 1)

    def test_undo_one_move_only_user(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()
        mock_ai.get_move.return_value = chess.Move.from_uci('e7e5')

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            user_move = chess.Move.from_uci('e2e4')
            self.session.board.push(user_move)
            self.session.history.append({'color': 'user', 'san': 'e4', 'fen': self.session.board.fen()})

            result = self.session.undo_move()
            self.assertEqual(len(self.session.history), 0)
            self.assertTrue(result['is_user_turn'])

    def test_undo_no_moves_error(self):
        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=MagicMock()):
            self.session.start_from_fen(chess.STARTING_FEN, user_color='white', difficulty='medium')
            self.session.history.clear()
            with self.assertRaises(PracticeError):
                self.session.undo_move()

    def test_get_hint(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()
        mock_ai.get_hint.return_value = {
            'hint_move': 'e4',
            'score': 0.3,
            'win_rate': 56.0,
        }

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            hint = self.session.get_hint()
            self.assertEqual(hint['hint_move'], 'e4')
            self.assertEqual(self.session.hints_used, 1)

    def test_get_hint_increments_counter(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()
        mock_ai.get_hint.return_value = {'hint_move': 'e4', 'score': 0.3, 'win_rate': 56.0}

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            self.session.get_hint()
            self.session.get_hint()
            self.session.get_hint()
            self.assertEqual(self.session.hints_used, 3)

    def test_resign(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            result = self.session.resign()
            self.assertTrue(result['is_game_over'])
            self.assertEqual(result['result'], '0-1')

    def test_resign_as_black(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()
        mock_ai.get_move.return_value = chess.Move.from_uci('e2e4')

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='black', difficulty='medium')
            result = self.session.resign()
            self.assertTrue(result['is_game_over'])
            self.assertEqual(result['result'], '1-0')

    def test_resign_game_over_error(self):
        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=MagicMock()):
            self.session.start_from_fen(chess.STARTING_FEN, user_color='white', difficulty='medium')
            self.session._game_over = True
            with self.assertRaises(PracticeError):
                self.session.resign()

    def test_get_status(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            status = self.session.get_status()
            self.assertTrue(status['active'])
            self.assertFalse(status['is_game_over'])
            self.assertEqual(status['user_color'], 'white')
            self.assertIn('history', status)
            self.assertIn('hints_used', status)
            self.assertIn('undo_count', status)

    def test_to_dict(self):
        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()

        self.session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            self.session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            d = self.session.to_dict()
            self.assertTrue(d['active'])
            self.assertEqual(d['user_color'], 'white')
            self.assertEqual(d['difficulty'], 'medium')
            self.assertIn('history', d)
            self.assertIn('hints_used', d)
            self.assertIn('undo_count', d)
            self.assertEqual(d['start_fen'], initial_fen)

    def test_start_from_fen_invalid(self):
        self.session._reset()
        with self.assertRaises(PracticeError):
            self.session.start_from_fen('invalid-fen-string', user_color='white', difficulty='medium')


class TestPracticeSessionCheckmate(unittest.TestCase):
    def test_scholars_mate(self):
        session = PracticeSession.__new__(PracticeSession)
        session.stockfish_path = 'stockfish'
        session.engine = None
        session.board = None
        session.user_color = None
        session.history = []
        session.ai_player = None
        session.difficulty = 'medium'
        session.hints_used = 0
        session.undo_count = 0
        session._start_fen = None
        session._game_over = False
        session._result = None
        session._source = None
        session._source_id = None

        fen = 'r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4'
        mock_ai = MagicMock()

        session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            session.start_from_fen(fen, user_color='white', difficulty='expert')
            result = session.user_move('Qxf7')
            self.assertTrue(result['is_checkmate'])
            self.assertTrue(result['is_game_over'])
            self.assertEqual(result['result'], '1-0')


class TestPracticeSessionUndoRebuild(unittest.TestCase):
    def test_undo_rebuilds_board_from_start_fen(self):
        session = PracticeSession.__new__(PracticeSession)
        session.stockfish_path = 'stockfish'
        session.engine = None
        session.board = None
        session.user_color = None
        session.history = []
        session.ai_player = None
        session.difficulty = 'medium'
        session.hints_used = 0
        session.undo_count = 0
        session._start_fen = None
        session._game_over = False
        session._result = None
        session._source = None
        session._source_id = None

        initial_fen = chess.STARTING_FEN
        mock_ai = MagicMock()
        mock_ai.get_move.return_value = chess.Move.from_uci('e7e5')

        session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            session.start_from_fen(initial_fen, user_color='white', difficulty='medium')
            session.user_move('e4')
            self.assertEqual(len(session.history), 2)

            mock_ai.get_move.return_value = chess.Move.from_uci('b8c6')
            session.user_move('Nf3')
            self.assertEqual(len(session.history), 4)

            result = session.undo_move()
            self.assertEqual(len(session.history), 2)
            self.assertTrue(result['is_user_turn'])
            self.assertEqual(session.undo_count, 1)


class TestPracticeSessionNoActive(unittest.TestCase):
    def test_user_move_no_session(self):
        session = PracticeSession.__new__(PracticeSession)
        session.board = None
        session._game_over = False
        with self.assertRaises(PracticeError):
            session.user_move('e4')

    def test_get_status_no_session(self):
        session = PracticeSession.__new__(PracticeSession)
        session.board = None
        status = session.get_status()
        self.assertFalse(status['active'])

    def test_to_dict_no_session(self):
        session = PracticeSession.__new__(PracticeSession)
        session.board = None
        d = session.to_dict()
        self.assertFalse(d['active'])


class TestPracticeSessionHistoryFormat(unittest.TestCase):
    def test_history_entries_have_required_fields(self):
        session = PracticeSession.__new__(PracticeSession)
        session.stockfish_path = 'stockfish'
        session.engine = None
        session.board = None
        session.user_color = None
        session.history = []
        session.ai_player = None
        session.difficulty = 'medium'
        session.hints_used = 0
        session.undo_count = 0
        session._start_fen = None
        session._game_over = False
        session._result = None
        session._source = None
        session._source_id = None

        mock_ai = MagicMock()
        mock_ai.get_move.return_value = chess.Move.from_uci('e7e5')

        session._reset()
        with patch('app.services.ai_player.AIPlayer', return_value=mock_ai):
            session.start_from_fen(chess.STARTING_FEN, user_color='white', difficulty='medium')
            session.user_move('e4')

            for entry in session.history:
                self.assertIn('color', entry)
                self.assertIn('san', entry)
                self.assertIn('fen', entry)
                self.assertIn(entry['color'], ['user', 'ai'])


if __name__ == '__main__':
    unittest.main()
