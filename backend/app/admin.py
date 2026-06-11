from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from app import db
from app.models.user import User
from app.models.game import Game
from app.models.player import Player
from app.models.analysis import Analysis
from app.models.opening import Opening
from app.models.practice import PracticeGame, Puzzle
from app.models.collection import Collection
from app.models.browsing_history import BrowsingHistory


class SecureModelView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    page_size = 20
    can_export = True


class UserAdmin(SecureModelView):
    form_columns = ['username', 'email', 'is_admin']
    column_list = ['id', 'username', 'email', 'is_admin', 'created_at']


class GameAdmin(SecureModelView):
    column_list = ['id', 'game_number', 'white_player_id', 'black_player_id', 'date', 'result', 'eco_code', 'total_moves']
    column_filters = ['result', 'eco_code', 'date']
    column_searchable_list = ['opening_name']


class PlayerAdmin(SecureModelView):
    column_list = ['id', 'name', 'elo_rating', 'title', 'country']
    column_searchable_list = ['name']


class OpeningAdmin(SecureModelView):
    column_list = ['id', 'eco_code', 'name', 'category', 'white_win_rate', 'black_win_rate', 'draw_rate']
    column_searchable_list = ['name', 'eco_code']


def setup_admin(app):
    admin = Admin(app, name='Chess Admin')
    admin.add_view(PlayerAdmin(Player, db.session, name='棋手', endpoint='admin_player'))
    admin.add_view(GameAdmin(Game, db.session, name='棋谱', endpoint='admin_game'))
    admin.add_view(SecureModelView(Analysis, db.session, name='分析', endpoint='admin_analysis'))
    admin.add_view(OpeningAdmin(Opening, db.session, name='开局库', endpoint='admin_opening'))
    admin.add_view(SecureModelView(Puzzle, db.session, name='残局', endpoint='admin_puzzle'))
    admin.add_view(SecureModelView(PracticeGame, db.session, name='练习历史', endpoint='admin_practice'))
    admin.add_view(SecureModelView(Collection, db.session, name='收藏', endpoint='admin_collection'))
    admin.add_view(SecureModelView(BrowsingHistory, db.session, name='浏览历史', endpoint='admin_browsing'))
    admin.add_view(UserAdmin(User, db.session, name='用户', endpoint='admin_user'))
    return admin
