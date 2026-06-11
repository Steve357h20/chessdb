import logging
import random
from io import StringIO
from typing import Optional

import chess
import chess.engine
import chess.pgn

logger = logging.getLogger(__name__)

DIFFICULTY_CONFIG = {
    'beginner': {'depth': 5, 'random_rate': 0.25, 'blunder_rate': 0.10, 'label': '入门'},
    'easy':     {'depth': 8, 'random_rate': 0.15, 'blunder_rate': 0.05, 'label': '初级'},
    'medium':   {'depth': 12, 'random_rate': 0.08, 'blunder_rate': 0.02, 'label': '中级'},
    'hard':     {'depth': 18, 'random_rate': 0.03, 'blunder_rate': 0.00, 'label': '高级'},
    'expert':   {'depth': 22, 'random_rate': 0.00, 'blunder_rate': 0.00, 'label': '专家'},
}


class AIPlayer:
    def __init__(self, stockfish_path: str = 'stockfish', difficulty: str = 'medium'):
        self.stockfish_path = stockfish_path
        self.difficulty = difficulty
        self.config = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG['medium'])
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self._is_mock = False

        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            self.engine.configure({'Threads': 2, 'Hash': 128})
            logger.info(
                'AIPlayer initialized: path=%s, difficulty=%s (%s), depth=%d',
                stockfish_path, difficulty, self.config['label'], self.config['depth'],
            )
        except Exception as e:
            logger.warning('Failed to initialize Stockfish for AIPlayer (path=%s, error=%s), using mock', stockfish_path, e)
            self.engine = None
            self._is_mock = True

    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        if self._is_mock:
            return self._mock_get_move(board)

        try:
            infos = self.engine.analyse(
                board,
                chess.engine.Limit(depth=self.config['depth']),
                multipv=5,
            )
        except chess.engine.EngineTerminatedError:
            self._restart_engine()
            infos = self.engine.analyse(
                board,
                chess.engine.Limit(depth=self.config['depth']),
                multipv=5,
            )

        candidates = []
        for info in infos:
            pv = info.get('pv', [])
            if pv:
                candidates.append(pv[0])

        if not candidates:
            legal = list(board.legal_moves)
            return legal[0] if legal else None

        best_move = candidates[0]

        if board.is_check():
            return best_move

        if board.is_capture(best_move) and len(infos) > 1:
            best_score = infos[0].get('score')
            second_score = infos[1].get('score')
            if best_score and second_score:
                try:
                    score_diff = best_score.relative.score(mate_score=100000) - second_score.relative.score(mate_score=100000)
                    if score_diff > 100:
                        return best_move
                except Exception:
                    pass

        roll = random.random()
        blunder_rate = self.config['blunder_rate']
        random_rate = self.config['random_rate']

        if board.is_check():
            return candidates[0]

        best_move = candidates[0]
        if board.is_capture(best_move) and len(infos) > 1:
            try:
                bs = infos[0].get('score').relative.score(mate_score=100000)
                ss = infos[1].get('score').relative.score(mate_score=100000)
                if bs - ss > 150:
                    return best_move
            except:
                pass

        if board.gives_check(best_move):
            if roll < blunder_rate * 0.3 and len(candidates) >= 3:
                return candidates[random.randint(2, min(4, len(candidates) - 1))]
            elif roll < blunder_rate * 0.3 + random_rate * 0.3 and len(candidates) >= 2:
                return candidates[1]
            return best_move

        if roll < blunder_rate and len(candidates) >= 3:
            idx = random.randint(2, min(4, len(candidates) - 1))
            return candidates[idx]
        elif roll < blunder_rate + random_rate and len(candidates) >= 2:
            return candidates[1]
        else:
            return candidates[0]

    def get_hint(self, board: chess.Board) -> dict:
        if self._is_mock:
            return self._mock_get_hint(board)

        try:
            infos = self.engine.analyse(
                board,
                chess.engine.Limit(depth=self.config['depth']),
                multipv=1,
            )
        except chess.engine.EngineTerminatedError:
            self._restart_engine()
            infos = self.engine.analyse(
                board,
                chess.engine.Limit(depth=self.config['depth']),
                multipv=1,
            )

        if not infos:
            return {'hint_move': None, 'score': 0.0, 'win_rate': 50.0}

        info = infos[0]
        pv_moves = info.get('pv', [])
        hint_san = None
        if pv_moves:
            try:
                hint_san = board.san(pv_moves[0])
            except Exception:
                hint_san = None

        raw_score = info.get('score')
        score = 0.0
        win_rate = 50.0

        if raw_score is not None:
            if raw_score.is_mate():
                mate_val = raw_score.relative.mate()
                score = 100.0 if (mate_val is not None and mate_val > 0) else -100.0
                win_rate = 99.9 if (mate_val is not None and mate_val > 0) else 0.1
            else:
                cp = raw_score.relative.score()
                if cp is not None:
                    score = cp / 100.0
                    win_rate = self._cp_to_win_rate(cp)

        return {
            'hint_move': hint_san,
            'score': round(score, 2),
            'win_rate': round(win_rate, 1),
        }

    def close(self):
        if self.engine and not self._is_mock:
            try:
                self.engine.quit()
            except Exception:
                pass
            self.engine = None
            logger.info('AIPlayer engine closed')

    def _mock_get_move(self, board: chess.Board) -> Optional[chess.Move]:
        legal = list(board.legal_moves)
        if not legal:
            return None
        if board.is_check():
            for m in legal:
                t = board.copy()
                t.push(m)
                if not t.is_check():
                    return m
        captures = [m for m in legal if board.is_capture(m)]
        if captures and random.random() < 0.7:
            return random.choice(captures)
        return random.choice(legal)

    def _mock_get_hint(self, board: chess.Board) -> dict:
        legal = list(board.legal_moves)
        if not legal:
            return {'hint_move': None, 'score': 0.0, 'win_rate': 50.0}
        move = legal[0]
        san = board.san(move)
        return {'hint_move': san, 'score': 0.0, 'win_rate': 50.0}

    def _cp_to_win_rate(self, cp: int) -> float:
        k = 0.004
        win_prob = 1.0 / (1.0 + pow(10, -cp * k))
        return win_prob * 100.0

    def _restart_engine(self):
        logger.warning('Restarting AIPlayer Stockfish engine')
        try:
            if self.engine:
                self.engine.quit()
        except Exception:
            pass
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            self.engine.configure({'Threads': 2, 'Hash': 128})
            logger.info('AIPlayer engine restarted successfully')
        except Exception as e:
            logger.error('Failed to restart AIPlayer engine: %s', e)
            self._is_mock = True
            self.engine = None

    def __del__(self):
        self.close()


class PracticeSession:
    def __init__(self, stockfish_path: str = 'stockfish'):
        self.stockfish_path = stockfish_path
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.board: Optional[chess.Board] = None
        self.user_color: Optional[str] = None
        self.history: list = []
        self.ai_player: Optional[AIPlayer] = None
        self.difficulty: str = 'medium'
        self.hints_used: int = 0
        self.undo_count: int = 0
        self._start_fen: Optional[str] = None
        self._game_over: bool = False
        self._result: Optional[str] = None
        self._source: Optional[str] = None
        self._source_id: Optional[int] = None

    def start_from_fen(self, fen: str, user_color: str = 'white', difficulty: str = 'medium') -> dict:
        self._reset()
        try:
            self.board = chess.Board(fen)
        except ValueError as e:
            raise PracticeError(f'Invalid FEN: {e}') from e

        self.user_color = user_color
        self.difficulty = difficulty
        self._start_fen = fen
        self.ai_player = AIPlayer(self.stockfish_path, difficulty)
        self._source = 'fen'

        user_turn = chess.WHITE if user_color == 'white' else chess.BLACK
        if self.board.turn != user_turn:
            ai_move = self.ai_player.get_move(self.board)
            if ai_move:
                ai_san = self.board.san(ai_move)
                self.board.push(ai_move)
                self.history.append({'color': 'ai', 'san': ai_san, 'fen': self.board.fen()})
                self._check_game_over()

        return {
            'fen': self.board.fen(),
            'turn': 'white' if self.board.turn == chess.WHITE else 'black',
            'is_user_turn': self.board.turn == user_turn,
        }

    def start_from_game(self, game_id: int, move_number: int = 0, user_color: str = 'white', difficulty: str = 'medium') -> dict:
        from app import db
        from app.models.game import Game

        game = Game.query.get(game_id)
        if not game:
            raise PracticeError(f'Game not found: {game_id}')

        if not game.pgn_content:
            raise PracticeError('Game has no PGN content')

        try:
            game_obj = chess.pgn.read_game(StringIO(game.pgn_content))
        except Exception as e:
            raise PracticeError(f'Failed to parse PGN: {e}') from e

        if game_obj is None:
            raise PracticeError('No valid game found in PGN')

        board = game_obj.board()
        node = game_obj
        ply = 0

        while node.variations and ply < move_number:
            next_node = node.variation(0)
            board.push(next_node.move)
            node = next_node
            ply += 1

        self._source = 'game'
        self._source_id = game_id

        return self.start_from_fen(board.fen(), user_color, difficulty)

    def start_from_puzzle(self, puzzle_id: int) -> dict:
        raise PracticeError('Puzzle mode not yet implemented')

    def user_move(self, san: str) -> dict:
        if self._game_over:
            raise PracticeError('Game is already over')
        if not self.board:
            raise PracticeError('No active session')

        try:
            move = self.board.parse_san(san)
        except (ValueError, chess.InvalidMoveError, chess.IllegalMoveError, chess.AmbiguousMoveError) as e:
            raise PracticeError(f'Invalid move: {san} - {e}') from e

        self.board.push(move)
        self.history.append({'color': 'user', 'san': san, 'fen': self.board.fen()})

        user_fen = self.board.fen()

        if self._check_game_over():
            return self._build_move_response(ai_move_san=None, user_fen=user_fen)

        ai_move = self.ai_player.get_move(self.board)
        if ai_move is None:
            self._check_game_over()
            return self._build_move_response(ai_move_san=None, user_fen=user_fen)

        ai_san = self.board.san(ai_move)
        self.board.push(ai_move)
        self.history.append({'color': 'ai', 'san': ai_san, 'fen': self.board.fen()})
        self._check_game_over()

        return self._build_move_response(ai_move_san=ai_san, user_fen=user_fen)

    def undo_move(self) -> dict:
        if not self.history:
            raise PracticeError('No moves to undo')
        if not self.board:
            raise PracticeError('No active session')

        if len(self.history) >= 2 and self.history[-1]['color'] == 'ai' and self.history[-2]['color'] == 'user':
            self.history.pop()
            self.history.pop()
        elif self.history[-1]['color'] == 'user':
            self.history.pop()
        elif self.history[-1]['color'] == 'ai':
            self.history.pop()

        self.undo_count += 1
        self._game_over = False
        self._result = None

        self.board = chess.Board(self._start_fen)
        for entry in self.history:
            move = self.board.parse_san(entry['san'])
            self.board.push(move)

        self._check_game_over()

        user_turn = chess.WHITE if self.user_color == 'white' else chess.BLACK
        is_user_turn = (self.board.turn == user_turn)

        return {
            'new_fen': self.board.fen(),
            'is_user_turn': is_user_turn,
        }

    def get_hint(self) -> dict:
        if not self.board:
            raise PracticeError('No active session')

        hint = self.ai_player.get_hint(self.board)
        self.hints_used += 1
        return hint

    def resign(self) -> dict:
        if self._game_over:
            raise PracticeError('Game is already over')
        if not self.board:
            raise PracticeError('No active session')

        self._game_over = True
        self._result = '0-1' if self.user_color == 'white' else '1-0'

        return {
            'is_game_over': True,
            'result': self._result,
        }

    def get_status(self) -> dict:
        if not self.board:
            return {'active': False}

        return {
            'active': True,
            'fen': self.board.fen(),
            'history': self.history,
            'result': self._result,
            'is_game_over': self._game_over,
            'is_check': self.board.is_check(),
            'is_checkmate': self.board.is_checkmate(),
            'is_stalemate': self.board.is_stalemate(),
            'user_color': self.user_color,
            'difficulty': self.difficulty,
            'hints_used': self.hints_used,
            'undo_count': self.undo_count,
        }

    def to_dict(self) -> dict:
        if not self.board:
            return {'active': False}

        return {
            'active': True,
            'fen': self.board.fen(),
            'start_fen': self._start_fen,
            'user_color': self.user_color,
            'difficulty': self.difficulty,
            'difficulty_label': DIFFICULTY_CONFIG.get(self.difficulty, {}).get('label', self.difficulty),
            'history': self.history,
            'hints_used': self.hints_used,
            'undo_count': self.undo_count,
            'is_game_over': self._game_over,
            'result': self._result,
            'source': self._source,
            'source_id': self._source_id,
        }

    def close(self):
        ai = getattr(self, 'ai_player', None)
        if ai:
            ai.close()
            self.ai_player = None

    def _reset(self):
        self.close()
        self.board = None
        self.user_color = None
        self.difficulty = 'medium'
        self.history = []
        self._start_fen = None
        self._game_over = False
        self._result = None
        self._source = None
        self._source_id = None
        self.hints_used = 0
        self.undo_count = 0

    def _check_game_over(self) -> bool:
        if self.board.is_checkmate():
            self._game_over = True
            self._result = '0-1' if self.board.turn == chess.WHITE else '1-0'
            return True
        if self.board.is_stalemate():
            self._game_over = True
            self._result = '1/2-1/2'
            return True
        if self.board.is_insufficient_material():
            self._game_over = True
            self._result = '1/2-1/2'
            return True
        if self.board.can_claim_fifty_moves():
            self._game_over = True
            self._result = '1/2-1/2'
            return True
        if self.board.can_claim_threefold_repetition():
            self._game_over = True
            self._result = '1/2-1/2'
            return True
        return False

    def _build_move_response(self, ai_move_san: Optional[str], user_fen: Optional[str] = None) -> dict:
        return {
            'ai_move': ai_move_san,
            'ai_move_san': ai_move_san,
            'user_fen': user_fen,
            'new_fen': self.board.fen(),
            'is_check': self.board.is_check(),
            'is_checkmate': self.board.is_checkmate(),
            'is_stalemate': self.board.is_stalemate(),
            'is_draw': self.board.is_stalemate() or self.board.is_insufficient_material(),
            'is_game_over': self._game_over,
            'result': self._result,
        }

    def __del__(self):
        self.close()


class PracticeError(Exception):
    pass
