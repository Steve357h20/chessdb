import unittest
from io import StringIO
from app.services.pgn_parser import PGNParser, PGNParsingError


class TestPGNParser(unittest.TestCase):
    def setUp(self):
        self.parser = PGNParser()

    def test_parse_simple_game(self):
        pgn = """[Event "Test"]
[Site "Test Site"]
[Date "2024.01.15"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"""

        result = self.parser.parse_content(pgn)

        self.assertEqual(result['game_info']['white'], 'Player1')
        self.assertEqual(result['game_info']['black'], 'Player2')
        self.assertEqual(result['game_info']['result'], '1-0')
        self.assertEqual(result['game_info']['eco'], '')
        self.assertEqual(result['total_moves'], 3)
        self.assertEqual(len(result['moves']), 3)

    def test_parse_game_with_eco(self):
        pgn = """[Event "Test"]
[Site "Test"]
[Date "2024.01.15"]
[White "A"]
[Black "B"]
[Result "1/2-1/2"]
[ECO "C42"]
[Opening "Petrov's Defense"]

1. e4 e5 2. Nf3 Nf6 1/2-1/2"""

        result = self.parser.parse_content(pgn)

        self.assertEqual(result['game_info']['eco'], 'C42')
        self.assertEqual(result['game_info']['opening'], "Petrov's Defense")

    def test_parse_game_with_elo(self):
        pgn = """[Event "Test"]
[Site "Test"]
[Date "2024.01.15"]
[White "A"]
[Black "B"]
[Result "*"]
[WhiteElo "2500"]
[BlackElo "2400"]

1. d4 d5 *"""

        result = self.parser.parse_content(pgn)

        self.assertEqual(result['game_info']['white_elo'], 2500)
        self.assertEqual(result['game_info']['black_elo'], 2400)

    def test_parse_invalid_pgn(self):
        result = self.parser.parse_content('not a valid pgn at all')
        self.assertEqual(result['total_moves'], 0)

    def test_parse_empty_content(self):
        with self.assertRaises(PGNParsingError):
            self.parser.parse_content('')

    def test_parse_multiple_games(self):
        pgn = """[Event "Game1"]
[Site "Test"]
[Date "2024.01.15"]
[White "A"]
[Black "B"]
[Result "1-0"]

1. e4 e5 1-0

[Event "Game2"]
[Site "Test"]
[Date "2024.01.15"]
[White "C"]
[Black "D"]
[Result "0-1"]

1. d4 d5 0-1"""

        games = PGNParser.parse_multiple_games(pgn)

        self.assertEqual(len(games), 2)
        self.assertEqual(games[0]['game_info']['white'], 'A')
        self.assertEqual(games[1]['game_info']['white'], 'C')

    def test_moves_structure(self):
        pgn = """[Event "Test"]
[Site "Test"]
[Date "2024.01.15"]
[White "A"]
[Black "B"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 *"""

        result = self.parser.parse_content(pgn)
        moves = result['moves']

        self.assertEqual(moves[0]['move_number'], 1)
        self.assertEqual(moves[0]['white'], 'e4')
        self.assertEqual(moves[0]['black'], 'e5')
        self.assertEqual(moves[1]['move_number'], 2)
        self.assertEqual(moves[1]['white'], 'Nf3')
        self.assertEqual(moves[1]['black'], 'Nc6')

    def test_to_fen_list(self):
        pgn = """[Event "Test"]
[Site "Test"]
[Date "2024.01.15"]
[White "A"]
[Black "B"]
[Result "*"]

1. e4 e5 *"""

        self.parser.parse_content(pgn)
        fen_list = self.parser.to_fen_list()

        self.assertEqual(len(fen_list), 3)
        self.assertIn('rnbqkbnr/pppppppp', fen_list[0])

    def test_pgn_to_dict_static(self):
        pgn = """[Event "Test"]
[Site "Test"]
[Date "2024.01.15"]
[White "A"]
[Black "B"]
[Result "1-0"]

1. e4 1-0"""

        result = PGNParser.pgn_to_dict(pgn)

        self.assertEqual(result['game_info']['white'], 'A')
        self.assertEqual(result['total_moves'], 1)

    def test_get_moves_list_before_parse(self):
        parser = PGNParser()
        self.assertEqual(parser.get_moves_list(), [])

    def test_get_game_info_before_parse(self):
        parser = PGNParser()
        self.assertEqual(parser.get_game_info(), {})

    def test_to_fen_list_before_parse(self):
        parser = PGNParser()
        self.assertEqual(parser.to_fen_list(), [])


if __name__ == '__main__':
    unittest.main()
