import logging
import re
from typing import Optional, Tuple

import chess

logger = logging.getLogger(__name__)

INITIAL_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

PIECE_UNICODE = {
    'K': '\u2654', 'Q': '\u2655', 'R': '\u2656', 'B': '\u2657', 'N': '\u2658', 'P': '\u2659',
    'k': '\u265A', 'q': '\u265B', 'r': '\u265C', 'b': '\u265D', 'n': '\u265E', 'p': '\u265F',
}

FILE_NAMES = 'abcdefgh'


def square_to_coords(square: str) -> Tuple[int, int]:
    if len(square) != 2:
        raise ValueError(f"Invalid square: {square}")
    file_char = square[0].lower()
    rank_char = square[1]
    if file_char < 'a' or file_char > 'h' or rank_char < '1' or rank_char > '8':
        raise ValueError(f"Invalid square: {square}")
    file_idx = ord(file_char) - ord('a')
    rank_idx = int(rank_char) - 1
    return (file_idx, rank_idx)


def coords_to_square(file_idx: int, rank_idx: int) -> str:
    if file_idx < 0 or file_idx > 7 or rank_idx < 0 or rank_idx > 7:
        raise ValueError(f"Invalid coordinates: ({file_idx}, {rank_idx})")
    return FILE_NAMES[file_idx] + str(rank_idx + 1)


def get_square_color(square: str) -> str:
    file_idx, rank_idx = square_to_coords(square)
    if (file_idx + rank_idx) % 2 == 1:
        return 'light'
    return 'dark'


class FENUtils:
    @staticmethod
    def parse_fen(fen_string: str) -> dict:
        if not FENUtils.is_valid_fen(fen_string):
            raise ValueError(f"Invalid FEN string: {fen_string}")

        parts = fen_string.split()
        piece_placement = parts[0]
        active_color = parts[1]
        castling_rights = parts[2]
        en_passant = parts[3]
        halfmove_clock = int(parts[4])
        fullmove_number = int(parts[5])

        board_array = FENUtils._piece_placement_to_array(piece_placement)

        castling = {
            'white_kingside': 'K' in castling_rights,
            'white_queenside': 'Q' in castling_rights,
            'black_kingside': 'k' in castling_rights,
            'black_queenside': 'q' in castling_rights,
        }

        return {
            'piece_placement': board_array,
            'active_color': active_color,
            'castling_rights': castling,
            'castling_string': castling_rights,
            'en_passant': en_passant,
            'halfmove_clock': halfmove_clock,
            'fullmove_number': fullmove_number,
        }

    @staticmethod
    def fen_to_board_array(fen: str) -> list:
        if not FENUtils.is_valid_fen(fen):
            raise ValueError(f"Invalid FEN string: {fen}")

        piece_placement = fen.split()[0]
        return FENUtils._piece_placement_to_array(piece_placement)

    @staticmethod
    def get_piece_at(fen: str, square: str) -> Optional[str]:
        if not FENUtils.is_valid_fen(fen):
            raise ValueError(f"Invalid FEN string: {fen}")

        board = chess.Board(fen)
        chess_square = chess.parse_square(square)
        piece = board.piece_at(chess_square)
        if piece is None:
            return None
        return piece.symbol()

    @staticmethod
    def make_move(fen: str, move: str) -> str:
        if not FENUtils.is_valid_fen(fen):
            raise ValueError(f"Invalid FEN string: {fen}")

        board = chess.Board(fen)

        try:
            chess_move = board.parse_san(move)
        except ValueError:
            try:
                chess_move = chess.Move.from_uci(move)
                if chess_move not in board.legal_moves:
                    raise ValueError(f"Illegal move: {move}")
            except ValueError:
                raise ValueError(f"Invalid move format: {move}")

        board.push(chess_move)
        return board.fen()

    @staticmethod
    def is_valid_fen(fen: str) -> bool:
        if not isinstance(fen, str):
            return False

        parts = fen.split()
        if len(parts) != 6:
            return False

        piece_placement, active_color, castling, en_passant, halfmove, fullmove = parts

        if active_color not in ('w', 'b'):
            return False

        if castling != '-':
            for c in castling:
                if c not in 'KQkq':
                    return False

        if en_passant != '-':
            if len(en_passant) != 2:
                return False
            if en_passant[0] not in 'abcdefgh' or en_passant[1] not in '36':
                return False

        try:
            hm = int(halfmove)
            fm = int(fullmove)
            if hm < 0 or fm < 1:
                return False
        except ValueError:
            return False

        ranks = piece_placement.split('/')
        if len(ranks) != 8:
            return False

        for rank in ranks:
            count = 0
            for c in rank:
                if c.isdigit():
                    count += int(c)
                elif c in 'pnbrqkPNBRQK':
                    count += 1
                else:
                    return False
            if count != 8:
                return False

        return True

    @staticmethod
    def board_to_fen(
        board_array: list,
        active_color: str = 'w',
        castling_rights: str = 'KQkq',
        en_passant: str = '-',
        halfmove_clock: int = 0,
        fullmove_number: int = 1,
    ) -> str:
        piece_placement = FENUtils._array_to_piece_placement(board_array)
        return f"{piece_placement} {active_color} {castling_rights} {en_passant} {halfmove_clock} {fullmove_number}"

    @staticmethod
    def _piece_placement_to_array(piece_placement: str) -> list:
        board = [[None] * 8 for _ in range(8)]
        ranks = piece_placement.split('/')

        for rank_idx, rank_str in enumerate(ranks):
            file_idx = 0
            for c in rank_str:
                if c.isdigit():
                    file_idx += int(c)
                else:
                    board[rank_idx][file_idx] = c
                    file_idx += 1

        return board

    @staticmethod
    def _array_to_piece_placement(board_array: list) -> str:
        ranks = []
        for rank in board_array:
            rank_str = ''
            empty = 0
            for cell in rank:
                if cell is None:
                    empty += 1
                else:
                    if empty > 0:
                        rank_str += str(empty)
                        empty = 0
                    rank_str += cell
            if empty > 0:
                rank_str += str(empty)
            ranks.append(rank_str)
        return '/'.join(ranks)

    @staticmethod
    def get_legal_moves(fen: str) -> list:
        if not FENUtils.is_valid_fen(fen):
            raise ValueError(f"Invalid FEN string: {fen}")

        board = chess.Board(fen)
        return [board.san(move) for move in board.legal_moves]

    @staticmethod
    def is_checkmate(fen: str) -> bool:
        if not FENUtils.is_valid_fen(fen):
            raise ValueError(f"Invalid FEN string: {fen}")
        board = chess.Board(fen)
        return board.is_checkmate()

    @staticmethod
    def is_stalemate(fen: str) -> bool:
        if not FENUtils.is_valid_fen(fen):
            raise ValueError(f"Invalid FEN string: {fen}")
        board = chess.Board(fen)
        return board.is_stalemate()

    @staticmethod
    def is_check(fen: str) -> bool:
        if not FENUtils.is_valid_fen(fen):
            raise ValueError(f"Invalid FEN string: {fen}")
        board = chess.Board(fen)
        return board.is_check()

    @staticmethod
    def get_king_square(fen: str, color: str) -> Optional[str]:
        if not FENUtils.is_valid_fen(fen):
            raise ValueError(f"Invalid FEN string: {fen}")

        board = chess.Board(fen)
        if color == 'w':
            king_square = board.king(chess.WHITE)
        else:
            king_square = board.king(chess.BLACK)

        if king_square is None:
            return None
        return chess.square_name(king_square)

    @staticmethod
    def board_to_unicode(fen: str) -> str:
        board_array = FENUtils.fen_to_board_array(fen)
        lines = []
        for rank_idx, rank in enumerate(board_array):
            row = f"{8 - rank_idx} "
            for cell in rank:
                if cell is None:
                    row += " . "
                else:
                    row += f" {PIECE_UNICODE.get(cell, cell)} "
            lines.append(row)
        lines.append("   a  b  c  d  e  f  g  h")
        return '\n'.join(lines)
