import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app import db
from app.models.player import Player
from app.models.game import Game

logger = logging.getLogger(__name__)

players_bp = Blueprint('players', __name__)


@players_bp.route('/filters', methods=['GET'])
def get_player_filters():
    """
    获取棋手筛选选项
    ---
    tags:
      - 棋手管理
    responses:
      200:
        description: 返回可用的头衔和国家筛选选项
    """
    titles = db.session.query(Player.title).filter(Player.title != '', Player.title.isnot(None)).distinct().order_by(Player.title).all()
    countries = db.session.query(Player.country).filter(Player.country != '', Player.country.isnot(None)).distinct().order_by(Player.country).all()
    return jsonify({
        'titles': [t[0] for t in titles if t[0]],
        'countries': [c[0] for c in countries if c[0]],
    })


@players_bp.route('', methods=['GET'])
def get_players():
    """
    获取棋手列表
    ---
    tags:
      - 棋手管理
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
      - name: search
        in: query
        type: string
        description: 姓名搜索
      - name: country
        in: query
        type: string
        description: 国家筛选
      - name: title
        in: query
        type: string
        description: 头衔筛选
      - name: min_elo
        in: query
        type: integer
        description: 最低等级分
      - name: max_elo
        in: query
        type: integer
        description: 最高等级分
      - name: sort
        in: query
        type: string
        default: elo_rating
      - name: order
        in: query
        type: string
        default: desc
    responses:
      200:
        description: 棋手列表
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    query = Player.query

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(Player.name.ilike(f'%{search}%'))

    country = request.args.get('country', '').strip()
    if country:
        query = query.filter(Player.country.ilike(f'%{country}%'))

    title = request.args.get('title', '').strip()
    if title:
        query = query.filter(Player.title == title)

    min_elo = request.args.get('min_elo', 0, type=int)
    if min_elo:
        query = query.filter(Player.elo_rating >= min_elo)

    max_elo = request.args.get('max_elo', 0, type=int)
    if max_elo:
        query = query.filter(Player.elo_rating <= max_elo)

    sort = request.args.get('sort', 'elo_rating')
    order = request.args.get('order', 'desc')

    if sort == 'name':
        sort_col = Player.name
    elif sort == 'elo_rating':
        sort_col = Player.elo_rating
    elif sort == 'created_at':
        sort_col = Player.created_at
    else:
        sort_col = Player.elo_rating

    if order == 'asc':
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
    })


@players_bp.route('/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """
    获取棋手详情
    ---
    tags:
      - 棋手管理
    parameters:
      - name: player_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 棋手详情
      404:
        description: 棋手不存在
    """
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404

    result = player.to_dict()
    result['stats'] = player.get_stats()

    return jsonify(result)


@players_bp.route('/<int:player_id>/games', methods=['GET'])
def get_player_games(player_id):
    """
    获取棋手的对局列表
    ---
    tags:
      - 棋手管理
    parameters:
      - name: player_id
        in: path
        type: integer
        required: true
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
      - name: color
        in: query
        type: string
        description: 执子颜色(white/black)
      - name: result
        in: query
        type: string
        description: 结果筛选
    responses:
      200:
        description: 对局列表
      404:
        description: 棋手不存在
    """
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    color = request.args.get('color', '').strip()

    if color == 'white':
        query = player.white_games
    elif color == 'black':
        query = player.black_games
    else:
        query = Game.query.filter(
            db.or_(Game.white_player_id == player_id, Game.black_player_id == player_id)
        )

    result_filter = request.args.get('result', '').strip()
    if result_filter:
        query = query.filter(Game.result == result_filter)

    query = query.order_by(Game.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [g.to_dict() for g in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
    })


@players_bp.route('/<int:player_id>/stats', methods=['GET'])
def get_player_stats(player_id):
    """
    获取棋手统计数据
    ---
    tags:
      - 棋手管理
    parameters:
      - name: player_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 统计数据(含ECO分类统计)
      404:
        description: 棋手不存在
    """
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404

    stats = player.get_stats()

    eco_stats = {}
    games = Game.query.filter(
        db.or_(Game.white_player_id == player_id, Game.black_player_id == player_id)
    ).all()

    for game in games:
        eco = game.eco_code[:1] if game.eco_code else 'Unknown'
        if eco not in eco_stats:
            eco_stats[eco] = {'total': 0, 'wins': 0, 'losses': 0, 'draws': 0}
        eco_stats[eco]['total'] += 1

        is_white = game.white_player_id == player_id
        if game.result == '1-0':
            if is_white:
                eco_stats[eco]['wins'] += 1
            else:
                eco_stats[eco]['losses'] += 1
        elif game.result == '0-1':
            if is_white:
                eco_stats[eco]['losses'] += 1
            else:
                eco_stats[eco]['wins'] += 1
        elif game.result == '1/2-1/2':
            eco_stats[eco]['draws'] += 1

    stats['eco_stats'] = eco_stats

    return jsonify(stats)
