import os
import sys
import time
import io
import click
import zstandard as zstd
import chess.pgn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.game import Game
from app.models.player import Player
from app.models.tournament import Tournament

app = create_app()

BATCH_SIZE = 500
MAX_GAMES = 0
MIN_ELO = 0

def get_or_create_player(name, elo=None):
    if not name or not name.strip():
        name = 'Unknown'
    name = name.strip()
    player = Player.query.filter_by(name=name).first()
    if not player:
        player = Player(name=name, elo_rating=elo or 0)
        db.session.add(player)
        db.session.flush()
    elif elo and elo > (player.elo_rating or 0):
        player.elo_rating = elo
    return player

def get_or_create_tournament(event, site=''):
    if not event or not event.strip():
        return None
    event = event.strip()
    tournament = Tournament.query.filter_by(name=event).first()
    if not tournament:
        tournament = Tournament(
            name=event,
            location=site.strip() if site else '',
            category='Imported',
        )
        db.session.add(tournament)
        db.session.flush()
    return tournament

@click.command()
@click.option('--file', 'pgn_file', required=True, help='Path to .pgn.zst or .pgn file')
@click.option('--max-games', default=MAX_GAMES, help='Maximum number of games to import')
@click.option('--batch-size', default=BATCH_SIZE, help='Batch size for database commits')
@click.option('--min-elo', default=MIN_ELO, help='Minimum ELO to import (both players)')
def import_pgn(pgn_file, max_games, batch_size, min_elo):
    with app.app_context():
        db.create_all()
        click.echo(f'Starting PGN import from: {pgn_file}')
        click.echo(f'Max games: {max_games}, Batch size: {batch_size}, Min ELO: {min_elo}')

        start_time = time.time()
        imported = 0
        skipped = 0
        errors = 0
        batch_count = 0

        open_fn = None
        if pgn_file.endswith('.zst'):
            dctx = zstd.ZstdDecompressor()
            raw_f = open(pgn_file, 'rb')
            reader = dctx.stream_reader(raw_f)
            text_stream = io.TextIOWrapper(reader, encoding='utf-8', errors='replace')
            open_fn = text_stream
        else:
            open_fn = open(pgn_file, 'r', encoding='utf-8', errors='replace')

        try:
            with open_fn as f:
                while max_games == 0 or imported < max_games:
                    game_obj = chess.pgn.read_game(f)
                    if game_obj is None:
                        click.echo('No more games in file.')
                        break

                    try:
                        h = game_obj.headers
                        white_elo_str = h.get('WhiteElo', '')
                        black_elo_str = h.get('BlackElo', '')

                        try:
                            white_elo = int(white_elo_str) if white_elo_str and white_elo_str.isdigit() else None
                        except ValueError:
                            white_elo = None
                        try:
                            black_elo = int(black_elo_str) if black_elo_str and black_elo_str.isdigit() else None
                        except ValueError:
                            black_elo = None

                        if min_elo > 0:
                            if (white_elo or 0) < min_elo or (black_elo or 0) < min_elo:
                                skipped += 1
                                continue

                        white_name = h.get('White', 'Unknown').strip()
                        black_name = h.get('Black', 'Unknown').strip()
                        result = h.get('Result', '*')
                        event = h.get('Event', '')
                        site = h.get('Site', '')
                        date = h.get('UTCDate', h.get('Date', ''))
                        eco = h.get('ECO', '')
                        opening = h.get('Opening', '')
                        termination = h.get('Termination', '')
                        time_control = h.get('TimeControl', '')

                        if date:
                            date = date.replace('??', '01').strip('.')

                        white_player = get_or_create_player(white_name, white_elo)
                        black_player = get_or_create_player(black_name, black_elo)
                        tournament = get_or_create_tournament(event, site)

                        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
                        pgn_str = game_obj.accept(exporter)

                        total_moves = 0
                        node = game_obj
                        while node.variations:
                            node = node.variation(0)
                            total_moves += 1
                        final_fen = node.board().fen()

                        game = Game(
                            white_player_id=white_player.id,
                            black_player_id=black_player.id,
                            tournament_id=tournament.id if tournament else None,
                            date=date,
                            result=result,
                            pgn_content=pgn_str,
                            eco_code=eco,
                            opening_name=opening,
                            total_moves=total_moves,
                            final_fen=final_fen,
                            white_elo=white_elo,
                            black_elo=black_elo,
                            termination=termination,
                            time_control=time_control,
                        )
                        db.session.add(game)
                        imported += 1
                        batch_count += 1

                        if batch_count >= batch_size:
                            db.session.commit()
                            elapsed = time.time() - start_time
                            click.echo(f'  Batch: {imported} imported, {skipped} skipped, {elapsed:.1f}s')
                            batch_count = 0

                    except Exception as e:
                        errors += 1
                        if errors <= 5:
                            click.echo(f'  Error: {e}')
                        db.session.rollback()

            if batch_count > 0:
                db.session.commit()

        except Exception as e:
            click.echo(f'Fatal error: {e}')

        elapsed = time.time() - start_time
        click.echo(f'\nDone! Imported: {imported}, Skipped: {skipped}, Errors: {errors}')
        click.echo(f'Time: {elapsed:.1f}s' + (f', Speed: {imported/elapsed:.1f} games/s' if elapsed > 0 else ''))

if __name__ == '__main__':
    import_pgn()
