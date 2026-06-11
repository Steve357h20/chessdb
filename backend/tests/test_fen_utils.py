import unittest
from app.services.fen_utils import FENUtils, square_to_coords, coords_to_square, get_square_color


INITIAL_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class TestSquareConversion(unittest.TestCase):
    def test_square_to_coords(self):
        self.assertEqual(square_to_coords('a1'), (0, 0))
        self.assertEqual(square_to_coords('h8'), (7, 7))
        self.assertEqual(square_to_coords('e4'), (4, 3))

    def test_square_to_coords_invalid(self):
        with self.assertRaises(ValueError):
            square_to_coords('i1')
        with self.assertRaises(ValueError):
            square_to_coords('a9')
        with self.assertRaises(ValueError):
            square_to_coords('a')

    def test_coords_to_square(self):
        self.assertEqual(coords_to_square(0, 0), 'a1')
        self.assertEqual(coords_to_square(7, 7), 'h8')
        self.assertEqual(coords_to_square(4, 3), 'e4')

    def test_coords_to_square_invalid(self):
        with self.assertRaises(ValueError):
            coords_to_square(-1, 0)
        with self.assertRaises(ValueError):
            coords_to_square(0, 8)

    def test_get_square_color(self):
        self.assertEqual(get_square_color('a1'), 'dark')
        self.assertEqual(get_square_color('a2'), 'light')
        self.assertEqual(get_square_color('b1'), 'light')
        self.assertEqual(get_square_color('h8'), 'dark')


class TestFENUtils(unittest.TestCase):
    def test_is_valid_fen_initial(self):
        self.assertTrue(FENUtils.is_valid_fen(INITIAL_FEN))

    def test_is_valid_fen_invalid(self):
        self.assertFalse(FENUtils.is_valid_fen(''))
        self.assertFalse(FENUtils.is_valid_fen('invalid'))
        self.assertFalse(FENUtils.is_valid_fen(None))
        self.assertFalse(FENUtils.is_valid_fen('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1'))

    def test_parse_fen(self):
        result = FENUtils.parse_fen(INITIAL_FEN)

        self.assertEqual(result['active_color'], 'w')
        self.assertEqual(result['castling_string'], 'KQkq')
        self.assertEqual(result['en_passant'], '-')
        self.assertEqual(result['halfmove_clock'], 0)
        self.assertEqual(result['fullmove_number'], 1)
        self.assertEqual(len(result['piece_placement']), 8)
        self.assertEqual(len(result['piece_placement'][0]), 8)

    def test_fen_to_board_array(self):
        board = FENUtils.fen_to_board_array(INITIAL_FEN)

        self.assertEqual(board[0][0], 'r')
        self.assertEqual(board[0][4], 'k')
        self.assertEqual(board[7][0], 'R')
        self.assertEqual(board[7][4], 'K')
        self.assertIsNone(board[4][4])

    def test_get_piece_at(self):
        self.assertEqual(FENUtils.get_piece_at(INITIAL_FEN, 'a1'), 'R')
        self.assertEqual(FENUtils.get_piece_at(INITIAL_FEN, 'e8'), 'k')
        self.assertEqual(FENUtils.get_piece_at(INITIAL_FEN, 'e4'), None)

    def test_make_move_san(self):
        after_e4 = FENUtils.make_move(INITIAL_FEN, 'e4')
        self.assertIn('4P3', after_e4)
        self.assertIn(' b ', after_e4)

        after_e4_e5 = FENUtils.make_move(after_e4, 'e5')
        self.assertIn('4p3', after_e4_e5)
        self.assertIn(' w ', after_e4_e5)

    def test_make_move_uci(self):
        after_e4 = FENUtils.make_move(INITIAL_FEN, 'e2e4')
        self.assertIn('4P3', after_e4)

    def test_make_move_invalid(self):
        with self.assertRaises(ValueError):
            FENUtils.make_move(INITIAL_FEN, 'Qxd4')

    def test_get_legal_moves(self):
        moves = FENUtils.get_legal_moves(INITIAL_FEN)

        self.assertIn('e4', moves)
        self.assertIn('d4', moves)
        self.assertIn('Nf3', moves)
        self.assertEqual(len(moves), 20)

    def test_is_checkmate(self):
        checkmate_fen = "rnb1kbnr/pppp1ppp/4p3/8/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        self.assertTrue(FENUtils.is_checkmate(checkmate_fen))

    def test_is_not_checkmate(self):
        self.assertFalse(FENUtils.is_checkmate(INITIAL_FEN))

    def test_is_stalemate(self):
        stalemate_fen = "5k2/5P2/5K2/8/8/8/8/8 b - - 0 1"
        self.assertTrue(FENUtils.is_stalemate(stalemate_fen))

    def test_is_check(self):
        check_fen = "4k3/8/8/8/8/8/8/4K2Q w - - 0 1"
        after_qh8 = FENUtils.make_move(check_fen, 'Qh8')
        self.assertTrue(FENUtils.is_check(after_qh8))

    def test_is_not_check(self):
        self.assertFalse(FENUtils.is_check(INITIAL_FEN))

    def test_board_to_fen(self):
        board = FENUtils.fen_to_board_array(INITIAL_FEN)
        result = FENUtils.board_to_fen(board)

        self.assertTrue(result.startswith('rnbqkbnr/pppppppp'))

    def test_get_king_square(self):
        self.assertEqual(FENUtils.get_king_square(INITIAL_FEN, 'w'), 'e1')
        self.assertEqual(FENUtils.get_king_square(INITIAL_FEN, 'b'), 'e8')

    def test_board_to_unicode(self):
        result = FENUtils.board_to_unicode(INITIAL_FEN)

        self.assertIn('♔', result)
        self.assertIn('♚', result)
        self.assertIn('a', result)
        self.assertIn('8', result)

    def test_parse_fen_after_moves(self):
        after_e4 = FENUtils.make_move(INITIAL_FEN, 'e4')
        result = FENUtils.parse_fen(after_e4)

        self.assertEqual(result['active_color'], 'b')
        self.assertEqual(result['castling_string'], 'KQkq')
        self.assertEqual(result['fullmove_number'], 1)


if __name__ == '__main__':
    unittest.main()
