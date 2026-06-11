import logging
from typing import Optional

import chess

from app.models.opening import Opening

logger = logging.getLogger(__name__)

CATEGORY_NAMES = {
    "A": "A - Flank Openings",
    "B": "B - Semi-Open Games",
    "C": "C - Open Games",
    "D": "D - Closed & Semi-Closed Games",
    "E": "E - Indian Defenses",
}

_FALLBACK_OPENINGS = {
    "A00": {
        "code": "A00", "name": "Polish (Orangutan) Opening", "variation": None,
        "moves": ["b4"], "category": "A",
        "description": "Also known as the Orangutan, an unconventional flank opening",
    },
    "A01": {
        "code": "A01", "name": "Nimzovich-Larsen Attack", "variation": None,
        "moves": ["b3"], "category": "A",
        "description": "A flexible flank opening with 1.b3, popularized by Nimzovich and Larsen",
    },
    "A04": {
        "code": "A04", "name": "Reti Opening", "variation": None,
        "moves": ["Nf3"], "category": "A",
        "description": "A hypermodern opening starting with 1.Nf3, controlling the center from a distance",
    },
    "A07": {
        "code": "A07", "name": "King's Indian Attack", "variation": None,
        "moves": ["Nf3", "d5", "g3"], "category": "A",
        "description": "White adopts a King's Indian Defense setup with reversed colors",
    },
    "A22": {
        "code": "A22", "name": "English Opening", "variation": "Four Knights",
        "moves": ["c4", "e5", "Nc3", "Nf6", "Nf3", "Nc6"], "category": "A",
        "description": "English Opening with an early knight development on both sides",
    },
    "B00": {
        "code": "B00", "name": "King's Pawn Defense", "variation": None,
        "moves": ["e4"], "category": "B",
        "description": "Uncommon responses to 1.e4",
    },
    "B20": {
        "code": "B20", "name": "Sicilian Defense", "variation": None,
        "moves": ["e4", "c5"], "category": "B",
        "description": "The most popular and combative response to 1.e4",
    },
    "B23": {
        "code": "B23", "name": "Sicilian Defense", "variation": "Closed",
        "moves": ["e4", "c5", "Nc3"], "category": "B",
        "description": "A positional approach against the Sicilian with 3.Nc3",
    },
    "B33": {
        "code": "B33", "name": "Sicilian Defense", "variation": "Sveshnikov",
        "moves": ["e4", "c5", "Nf3", "Nc6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "e5"], "category": "B",
        "description": "One of the sharpest Sicilian variations, featuring early e5 push",
    },
    "B40": {
        "code": "B40", "name": "Sicilian Defense", "variation": "French Variation",
        "moves": ["e4", "c5", "Nf3", "e6"], "category": "B",
        "description": "A hybrid Sicilian-French setup with ...e6",
    },
    "B90": {
        "code": "B90", "name": "Sicilian Defense", "variation": "Najdorf",
        "moves": ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6"], "category": "B",
        "description": "The Najdorf is the most popular and theoretically significant Sicilian line",
    },
    "B12": {
        "code": "B12", "name": "Caro-Kann Defense", "variation": "Advance Variation",
        "moves": ["e4", "c6", "d4", "d5", "e5"], "category": "B",
        "description": "A solid defense with 1...c6 followed by 2...d5, Advance Variation",
    },
    "B14": {
        "code": "B14", "name": "Caro-Kann Defense", "variation": "Classical Variation",
        "moves": ["e4", "c6", "d4", "d5", "Nc3"], "category": "B",
        "description": "The Classical Variation of the Caro-Kann with Nc3",
    },
    "C20": {
        "code": "C20", "name": "King's Pawn Game", "variation": None,
        "moves": ["e4", "e5"], "category": "C",
        "description": "The Open Game, starting with 1.e4 e5",
    },
    "C42": {
        "code": "C42", "name": "Petrov's Defense", "variation": None,
        "moves": ["e4", "e5", "Nf3", "Nf6"], "category": "C",
        "description": "Also called the Russian Defense, a solid counter-attacking system",
    },
    "C44": {
        "code": "C44", "name": "Scotch Game", "variation": None,
        "moves": ["e4", "e5", "Nf3", "Nc6", "d4"], "category": "C",
        "description": "An open game where White immediately challenges the center with d4",
    },
    "C50": {
        "code": "C50", "name": "Giuoco Piano", "variation": None,
        "moves": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5"], "category": "C",
        "description": "The Italian Game, one of the oldest chess openings",
    },
    "C55": {
        "code": "C55", "name": "Two Knights Defense", "variation": None,
        "moves": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6"], "category": "C",
        "description": "A sharp variation of the Italian Game with 3...Nf6",
    },
    "C60": {
        "code": "C60", "name": "Ruy Lopez", "variation": None,
        "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5"], "category": "C",
        "description": "The Spanish Game, one of the most important and popular openings",
    },
    "C67": {
        "code": "C67", "name": "Ruy Lopez", "variation": "Berlin Defense",
        "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5", "Nf6"], "category": "C",
        "description": "The Berlin Wall, a solid defense that became extremely popular at top level",
    },
    "C84": {
        "code": "C84", "name": "Ruy Lopez", "variation": "Closed",
        "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O", "Be7"], "category": "C",
        "description": "The Closed Ruy Lopez, the most classical and positional variation",
    },
    "C41": {
        "code": "C41", "name": "Philidor Defense", "variation": None,
        "moves": ["e4", "e5", "Nf3", "d6"], "category": "C",
        "description": "A solid but passive defense with 2...d6",
    },
    "D02": {
        "code": "D02", "name": "Queen's Pawn Game", "variation": None,
        "moves": ["d4"], "category": "D",
        "description": "Starting with 1.d4, the Queen's Pawn Opening",
    },
    "D35": {
        "code": "D35", "name": "Queen's Gambit Declined", "variation": None,
        "moves": ["d4", "d5", "c4", "e6", "Nc3", "Nf6"], "category": "D",
        "description": "One of the most solid and classical defenses against the Queen's Gambit",
    },
    "D37": {
        "code": "D37", "name": "Queen's Gambit Declined", "variation": "4.Nc3",
        "moves": ["d4", "d5", "c4", "e6", "Nc3", "Nf6", "Bf4"], "category": "D",
        "description": "The Ragozin variation with Bf4, a flexible QGD system",
    },
    "D06": {
        "code": "D06", "name": "Queen's Gambit", "variation": None,
        "moves": ["d4", "d5", "c4"], "category": "D",
        "description": "The Queen's Gambit, offering a wing pawn for central control",
    },
    "D44": {
        "code": "D44", "name": "Semi-Slav Defense", "variation": "Botvinnik Variation",
        "moves": ["d4", "d5", "c4", "e6", "Nc3", "Nf6", "Nf3", "c6", "Bg5", "dxc4"], "category": "D",
        "description": "One of the most complex and theoretical openings in chess",
    },
    "E15": {
        "code": "E15", "name": "Queen's Indian Defense", "variation": None,
        "moves": ["d4", "Nf6", "c4", "e6", "Nf3", "b6"], "category": "E",
        "description": "A solid hypermodern defense with ...b6 controlling e4 from the flank",
    },
    "E60": {
        "code": "E60", "name": "King's Indian Defense", "variation": None,
        "moves": ["d4", "Nf6", "c4", "g6"], "category": "E",
        "description": "A dynamic defense where Black allows White to occupy the center then attacks it",
    },
    "E94": {
        "code": "E94", "name": "King's Indian Defense", "variation": "Classical",
        "moves": ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6", "Nf3", "O-O", "Be2", "e5"], "category": "E",
        "description": "The Classical King's Indian, featuring an early e5 by Black",
    },
    "E11": {
        "code": "E11", "name": "Bogo-Indian Defense", "variation": None,
        "moves": ["d4", "Nf6", "c4", "e6", "Nf3", "Bb4+"], "category": "E",
        "description": "A solid response to 1.d4 with an early Bb4+ check",
    },
    "E32": {
        "code": "E32", "name": "Nimzo-Indian Defense", "variation": "Classical",
        "moves": ["d4", "Nf6", "c4", "e6", "Nc3", "Bb4", "Qc2"], "category": "E",
        "description": "The Classical Variation of the Nimzo-Indian with Qc2",
    },
}


class OpeningRecognizer:
    def __init__(self):
        self._openings = {}
        self._load_from_database()
        self._move_prefixes = self._build_move_prefixes()
        logger.info("OpeningRecognizer initialized with %d openings", len(self._openings))

    def _load_from_database(self):
        try:
            openings = Opening.query.all()
            for o in openings:
                self._openings[o.eco_code] = {
                    'code': o.eco_code, 'name': o.name,
                    'variation': o.variation, 'moves': o.get_moves_list(),
                    'category': o.category, 'description': o.description,
                }
            if self._openings:
                return
        except Exception:
            pass
        self._openings = self._get_fallback_openings()

    def _get_fallback_openings(self):
        return dict(_FALLBACK_OPENINGS)

    def identify_opening(self, pgn_moves: list) -> dict:
        if not pgn_moves:
            return self._unknown_opening()

        san_moves = self._normalize_moves(pgn_moves)

        best_match = None
        best_matched_count = 0
        best_total_moves = 0

        for eco_code, opening in self._openings.items():
            opening_moves = opening["moves"]
            match_count = self._count_matching_moves(san_moves, opening_moves)

            if match_count > best_matched_count:
                best_matched_count = match_count
                best_match = opening
                best_total_moves = len(opening_moves)
            elif match_count == best_matched_count and best_match is not None and match_count > 0:
                if len(opening_moves) <= len(san_moves) and best_total_moves > len(san_moves):
                    best_match = opening
                    best_total_moves = len(opening_moves)
                elif len(opening_moves) <= len(san_moves) and best_total_moves <= len(san_moves):
                    if len(opening_moves) > best_total_moves:
                        best_match = opening
                        best_total_moves = len(opening_moves)

        if best_match is None or best_matched_count == 0:
            return self._unknown_opening()

        total_opening_moves = len(best_match["moves"])
        confidence = min(best_matched_count / total_opening_moves, 1.0)

        if best_matched_count < total_opening_moves:
            confidence *= 0.7

        if best_matched_count >= 4:
            confidence = max(confidence, 0.8)
        elif best_matched_count >= 2:
            confidence = max(confidence, 0.5)

        return {
            "eco_code": best_match["code"],
            "name": best_match["name"],
            "variation": best_match.get("variation"),
            "confidence": round(confidence, 2),
            "matched_moves": best_matched_count,
            "description": best_match.get("description", ""),
            "category": CATEGORY_NAMES.get(best_match["category"], best_match["category"]),
        }

    def get_eco_info(self, eco_code: str) -> dict:
        eco = eco_code.upper().strip()
        opening = self._openings.get(eco)
        if opening:
            return {
                "eco_code": opening["code"],
                "name": opening["name"],
                "variation": opening.get("variation"),
                "moves": opening["moves"],
                "category": CATEGORY_NAMES.get(opening["category"], opening["category"]),
                "description": opening.get("description", ""),
            }

        cat = eco[0] if eco else ''
        if cat in CATEGORY_NAMES:
            return {
                "eco_code": eco,
                "name": f"Opening {eco}",
                "variation": None,
                "moves": [],
                "category": CATEGORY_NAMES[cat],
                "description": f"ECO code {eco} - {CATEGORY_NAMES[cat]}",
            }

        return {"error": f"ECO code {eco_code} not found"}

    def find_similar_openings(self, moves: list, top_k: int = 3) -> list:
        san_moves = self._normalize_moves(moves)
        results = []

        for eco_code, opening in self._openings.items():
            match_count = self._count_matching_moves(san_moves, opening["moves"])
            if match_count > 0:
                total = len(opening["moves"])
                similarity = match_count / total
                results.append({
                    "eco_code": opening["code"],
                    "name": opening["name"],
                    "variation": opening.get("variation"),
                    "similarity": round(similarity, 2),
                    "matched_moves": match_count,
                    "total_moves": total,
                    "category": CATEGORY_NAMES.get(opening["category"], opening["category"]),
                })

        results.sort(key=lambda x: (x["matched_moves"], x["similarity"]), reverse=True)
        return results[:top_k]

    def get_opening_tree(self) -> dict:
        tree = {}
        for eco_code, opening in self._openings.items():
            category = opening["category"]
            if category not in tree:
                tree[category] = {
                    "name": CATEGORY_NAMES.get(category, category),
                    "openings": [],
                }
            tree[category]["openings"].append({
                "eco_code": opening["code"],
                "name": opening["name"],
                "variation": opening.get("variation"),
                "moves": opening["moves"],
            })
        return tree

    def _build_move_prefixes(self) -> dict:
        prefixes = {}
        for eco_code, opening in self._openings.items():
            moves = opening["moves"]
            for i in range(1, len(moves) + 1):
                prefix = tuple(moves[:i])
                if prefix not in prefixes:
                    prefixes[prefix] = []
                prefixes[prefix].append(eco_code)
        return prefixes

    def _normalize_moves(self, moves: list) -> list:
        normalized = []
        for move in moves:
            if isinstance(move, str):
                move = move.strip()
                move = move.rstrip('+#!?')
                normalized.append(move)
            else:
                normalized.append(str(move))
        return normalized

    def _count_matching_moves(self, played_moves: list, opening_moves: list) -> int:
        count = 0
        for i in range(min(len(played_moves), len(opening_moves))):
            played = played_moves[i].rstrip('+#!?')
            reference = opening_moves[i].rstrip('+#!?')
            if played.lower() == reference.lower():
                count += 1
            else:
                break
        return count

    def _unknown_opening(self) -> dict:
        return {
            "eco_code": "",
            "name": "Unknown Opening",
            "variation": None,
            "confidence": 0.0,
            "matched_moves": 0,
            "description": "",
            "category": "",
        }
