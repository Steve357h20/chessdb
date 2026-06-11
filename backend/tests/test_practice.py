import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import json
import chess

from app.services.puzzle_library import (
    get_all_puzzles, get_puzzles_by_category,
    get_puzzles_by_difficulty, get_puzzle, PUZZLE_LIBRARY,
)
from app.models.practice import PracticeGame


class TestPuzzleLibrary(unittest.TestCase):
    def test_puzzle_library_has_10_entries(self):
        self.assertEqual(len(PUZZLE_LIBRARY), 10)

    def test_all_puzzles_have_required_fields(self):
        required = {'name', 'category', 'difficulty', 'description', 'fen', 'hint'}
        for pid, pdata in PUZZLE_LIBRARY.items():
            missing = required - set(pdata.keys())
            self.assertFalse(missing, f'Puzzle {pid} missing fields: {missing}')

    def test_all_fens_are_valid(self):
        for pid, pdata in PUZZLE_LIBRARY.items():
            try:
                board = chess.Board(pdata['fen'])
                self.assertTrue(board.is_valid(), f'Puzzle {pid} has invalid board state')
            except ValueError as e:
                self.fail(f'Puzzle {pid} has invalid FEN: {e}')

    def test_all_difficulties_are_valid(self):
        valid = {'beginner', 'easy', 'medium', 'hard'}
        for pid, pdata in PUZZLE_LIBRARY.items():
            self.assertIn(pdata['difficulty'], valid, f'Puzzle {pid} has invalid difficulty')

    def test_all_categories_are_valid(self):
        valid = {'残局', '战术', '开局', '将杀'}
        for pid, pdata in PUZZLE_LIBRARY.items():
            self.assertIn(pdata['category'], valid, f'Puzzle {pid} has invalid category')

    def test_get_all_puzzles(self):
        result = get_all_puzzles()
        self.assertEqual(len(result), 10)
        self.assertIn('endgame_king_pawn', result)

    def test_get_puzzles_by_category(self):
        result = get_puzzles_by_category('残局')
        self.assertTrue(len(result) >= 3)
        for pid, pdata in result.items():
            self.assertEqual(pdata['category'], '残局')

    def test_get_puzzles_by_difficulty(self):
        result = get_puzzles_by_difficulty('beginner')
        self.assertTrue(len(result) >= 2)
        for pid, pdata in result.items():
            self.assertEqual(pdata['difficulty'], 'beginner')

    def test_get_puzzle_exists(self):
        result = get_puzzle('endgame_king_pawn')
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], '王兵残局')

    def test_get_puzzle_not_exists(self):
        result = get_puzzle('nonexistent_puzzle')
        self.assertIsNone(result)

    def test_specific_puzzles_exist(self):
        expected_ids = [
            'endgame_king_pawn', 'endgame_rook', 'endgame_queen_vs_rook',
            'tactic_fork', 'tactic_pin', 'tactic_discovered_attack',
            'opening_scholar_mate', 'endgame_bishop_pair',
            'mate_in_two_1', 'mate_in_two_2',
        ]
        for pid in expected_ids:
            self.assertIn(pid, PUZZLE_LIBRARY, f'Missing puzzle: {pid}')


class TestPracticeGameModel(unittest.TestCase):
    def test_to_dict_returns_required_fields(self):
        pg = PracticeGame(
            mode='puzzle',
            puzzle_id='endgame_king_pawn',
            start_fen='8/8/8/8/8/5k2/4P3/4K3 w - - 0 1',
            user_color='w',
            difficulty='beginner',
            moves_json='[]',
            final_fen='8/8/8/8/8/5k2/4P3/4K3 w - - 0 1',
            result='*',
            total_moves=0,
            hints_used=0,
            undo_count=0,
        )
        d = pg.to_dict()
        required_fields = [
            'id', 'user_id', 'mode', 'puzzle_id', 'source_game_id',
            'from_move', 'start_fen', 'user_color', 'difficulty',
            'moves', 'final_fen', 'result', 'total_moves',
            'hints_used', 'undo_count', 'duration_seconds', 'created_at',
        ]
        for field in required_fields:
            self.assertIn(field, d, f'Missing field: {field}')

    def test_moves_json_parsed_correctly(self):
        moves = [
            {'color': 'user', 'san': 'e4', 'fen': '...'},
            {'color': 'ai', 'san': 'e5', 'fen': '...'},
        ]
        pg = PracticeGame(moves_json=json.dumps(moves))
        d = pg.to_dict()
        self.assertEqual(len(d['moves']), 2)
        self.assertEqual(d['moves'][0]['san'], 'e4')

    def test_invalid_moves_json_returns_empty_list(self):
        pg = PracticeGame(moves_json='invalid json')
        d = pg.to_dict()
        self.assertEqual(d['moves'], [])

    def test_empty_moves_json(self):
        pg = PracticeGame(moves_json='')
        d = pg.to_dict()
        self.assertEqual(d['moves'], [])


class TestPracticeAPIEndpoints(unittest.TestCase):
    def test_puzzle_library_imports(self):
        from app.services.puzzle_library import PUZZLE_LIBRARY
        self.assertIsInstance(PUZZLE_LIBRARY, dict)

    def test_practice_session_imports(self):
        from app.services.ai_player import PracticeSession, PracticeError
        self.assertTrue(callable(PracticeSession))
        self.assertTrue(issubclass(PracticeError, Exception))

    def test_practice_model_imports(self):
        from app.models.practice import PracticeGame
        self.assertTrue(hasattr(PracticeGame, 'to_dict'))

    def test_practice_route_imports(self):
        from app.routes.practice import practice_bp
        self.assertEqual(practice_bp.name, 'practice')


if __name__ == '__main__':
    unittest.main()
