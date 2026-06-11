import logging
import re
from io import StringIO
from typing import Optional

import chess
import chess.pgn

logger = logging.getLogger(__name__)


class PGNParser:
    def __init__(self):
        self._game: Optional[chess.pgn.Game] = None
        self._game_info: Optional[dict] = None
        self._moves: Optional[list] = None
        self._fen_list: Optional[list] = None
        self._final_fen: Optional[str] = None
        self._total_moves: int = 0

    def parse_file(self, file_path: str) -> dict:
        logger.info("Parsing PGN file: %s", file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_content(content)
        except FileNotFoundError:
            logger.error("PGN file not found: %s", file_path)
            raise
        except UnicodeDecodeError:
            logger.info("Retrying with latin-1 encoding: %s", file_path)
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return self.parse_content(content)

    def parse_content(self, pgn_string: str) -> dict:
        logger.info("Parsing PGN content (length=%d)", len(pgn_string))
        self._reset()

        try:
            game = chess.pgn.read_game(StringIO(pgn_string))
        except Exception as e:
            logger.error("Failed to parse PGN: %s", e)
            raise PGNParsingError(f"Failed to parse PGN: {e}") from e

        if game is None:
            logger.error("No valid game found in PGN content")
            raise PGNParsingError("No valid game found in PGN content")

        self._game = game
        self._game_info = self._extract_game_info(game)
        self._moves = self._extract_moves(game)
        self._final_fen = game.board().fen() if game.end().board() is None else game.end().board().fen()
        self._total_moves = len(self._moves)

        result = {
            "game_info": self._game_info,
            "moves": self._moves,
            "final_fen": self._final_fen,
            "total_moves": self._total_moves,
        }

        logger.info(
            "Parsed game: %s vs %s, %d moves, result=%s",
            self._game_info.get("white", "?"),
            self._game_info.get("black", "?"),
            self._total_moves,
            self._game_info.get("result", "*"),
        )
        return result

    def get_moves_list(self) -> list:
        if self._moves is None:
            logger.warning("No game parsed yet, call parse_content() first")
            return []
        return self._moves

    def get_game_info(self) -> dict:
        if self._game_info is None:
            logger.warning("No game parsed yet, call parse_content() first")
            return {}
        return self._game_info

    def to_fen_list(self) -> list:
        if self._game is None:
            logger.warning("No game parsed yet, call parse_content() first")
            return []

        if self._fen_list is not None:
            return self._fen_list

        self._fen_list = []
        board = self._game.board()
        self._fen_list.append(board.fen())

        node = self._game
        while node.variations:
            next_node = node.variation(0)
            board = next_node.board()
            self._fen_list.append(board.fen())
            node = next_node

        return self._fen_list

    def _reset(self):
        self._game = None
        self._game_info = None
        self._moves = None
        self._fen_list = None
        self._final_fen = None
        self._total_moves = 0

    def _extract_game_info(self, game: chess.pgn.Game) -> dict:
        headers = game.headers
        info = {
            "event": headers.get("Event", ""),
            "site": headers.get("Site", ""),
            "date": headers.get("Date", ""),
            "round": headers.get("Round", ""),
            "white": headers.get("White", ""),
            "black": headers.get("Black", ""),
            "result": headers.get("Result", "*"),
            "eco": headers.get("ECO", ""),
            "opening": headers.get("Opening", ""),
            "variation": headers.get("Variation", ""),
        }

        white_elo = headers.get("WhiteElo", "")
        black_elo = headers.get("BlackElo", "")
        info["white_elo"] = int(white_elo) if white_elo and white_elo.isdigit() else 0
        info["black_elo"] = int(black_elo) if black_elo and black_elo.isdigit() else 0

        for key in ["Annotator", "PlyCount", "TimeControl", "Termination"]:
            if key in headers:
                info[key.lower()] = headers[key]

        return info

    def _extract_moves(self, game: chess.pgn.Game) -> list:
        moves = []
        board = game.board()
        node = game
        move_number = 0

        while node.variations:
            next_node = node.variation(0)
            move = next_node.move
            san = board.san(move)

            comment = next_node.comment.strip() if next_node.comment else ""
            nags = list(next_node.nags) if next_node.nags else []

            if board.turn:
                move_number += 1
                moves.append({
                    "move_number": move_number,
                    "white": san,
                    "black": None,
                    "white_fen": next_node.board().fen(),
                    "black_fen": None,
                    "white_comment": comment,
                    "black_comment": None,
                    "white_nags": nags,
                    "black_nags": [],
                })
            else:
                if moves:
                    moves[-1]["black"] = san
                    moves[-1]["black_fen"] = next_node.board().fen()
                    moves[-1]["black_comment"] = comment
                    moves[-1]["black_nags"] = nags

            board.push(move)
            node = next_node

        return moves

    @staticmethod
    def parse_multiple_games(pgn_string: str) -> list:
        logger.info("Parsing multiple games from PGN content")
        games = []
        pgn_io = StringIO(pgn_string)

        while True:
            try:
                game = chess.pgn.read_game(pgn_io)
            except Exception as e:
                logger.warning("Error parsing game: %s", e)
                break

            if game is None:
                break

            parser = PGNParser()
            parser._game = game
            parser._game_info = parser._extract_game_info(game)
            parser._moves = parser._extract_moves(game)
            parser._final_fen = game.end().board().fen()
            parser._total_moves = len(parser._moves)

            games.append({
                "game_info": parser._game_info,
                "moves": parser._moves,
                "final_fen": parser._final_fen,
                "total_moves": parser._total_moves,
            })

        logger.info("Parsed %d games from PGN content", len(games))
        return games

    @staticmethod
    def pgn_to_dict(pgn_string: str) -> dict:
        parser = PGNParser()
        return parser.parse_content(pgn_string)


class PGNParsingError(Exception):
    pass
