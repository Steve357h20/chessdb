import logging

from flask import jsonify
from app import db

logger = logging.getLogger(__name__)


def register_index_route(app):
    @app.route('/')
    def index():
        from app.models.game import Game
        from app.models.player import Player
        from app.models.analysis import Analysis
        from app.models.opening import Opening
        from app.models.practice import PracticeGame, Puzzle
        from app.models.user import User

        stats = {
            'games': Game.query.count(),
            'players': Player.query.count(),
            'analyses': Analysis.query.count(),
            'openings': Opening.query.count(),
            'puzzles': Puzzle.query.count(),
            'practice_games': PracticeGame.query.count(),
            'users': User.query.count(),
        }
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith('/api/'):
                routes.append({
                    'path': rule.rule,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                })
        return jsonify({
            'name': 'Chess Data Management API',
            'version': '1.0.0',
            'status': 'running',
            'database': stats,
            'api_routes': routes,
        })


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'detail': str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized', 'detail': str(e)}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden', 'detail': str(e)}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found', 'detail': str(e)}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed', 'detail': str(e)}), 405

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        logger.error("Internal server error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500


def register_blueprints(app):
    register_index_route(app)

    from app.routes.games import games_bp
    from app.routes.players import players_bp
    from app.routes.analysis import analysis_bp
    from app.routes.openings import openings_bp
    from app.routes.auth import auth_bp
    from app.routes.collections import collections_bp
    from app.routes.practice import practice_bp
    from app.routes.browsing import browsing_bp

    app.register_blueprint(games_bp, url_prefix='/api/games')
    app.register_blueprint(players_bp, url_prefix='/api/players')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(openings_bp, url_prefix='/api/openings')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(collections_bp, url_prefix='/api/collections')
    app.register_blueprint(practice_bp, url_prefix='/api/practice')
    app.register_blueprint(browsing_bp, url_prefix='/api/browsing')
