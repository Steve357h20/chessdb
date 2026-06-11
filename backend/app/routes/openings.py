import logging

from flask import Blueprint, request, jsonify

from app import db
from app.models.opening import Opening
from app.models.game import Game
from app.services.opening_recognizer import OpeningRecognizer

logger = logging.getLogger(__name__)

openings_bp = Blueprint('openings', __name__)

_recognizer = None


def _get_recognizer():
    global _recognizer
    if _recognizer is None:
        _recognizer = OpeningRecognizer()
    return _recognizer


@openings_bp.route('', methods=['GET'])
def get_openings():
    """
    获取开局库列表
    ---
    tags:
      - 开局管理
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
      - name: category
        in: query
        type: string
        description: 分类筛选
      - name: search
        in: query
        type: string
        description: 名称/ECO代码搜索
      - name: eco
        in: query
        type: string
        description: ECO代码前缀筛选
      - name: sort
        in: query
        type: string
        default: eco_code
      - name: order
        in: query
        type: string
        default: asc
    responses:
      200:
        description: 开局列表
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    query = Opening.query

    category = request.args.get('category', '').strip()
    if category:
        query = query.filter(Opening.category == category)

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(
            db.or_(
                Opening.name.ilike(f'%{search}%'),
                Opening.eco_code.ilike(f'%{search}%'),
                Opening.variation.ilike(f'%{search}%'),
            )
        )

    eco = request.args.get('eco', '').strip()
    if eco:
        query = query.filter(Opening.eco_code.ilike(f'{eco}%'))

    sort = request.args.get('sort', 'eco_code').strip()
    order = request.args.get('order', 'asc').strip()

    sort_map = {
        'eco_code': Opening.eco_code,
        'name': Opening.name,
        'white_win_rate': Opening.white_win_rate,
        'black_win_rate': Opening.black_win_rate,
        'draw_rate': Opening.draw_rate,
        'popularity': Opening.popularity,
    }
    sort_col = sort_map.get(sort, Opening.eco_code)

    if order == 'desc':
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [o.to_dict() for o in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
    })


@openings_bp.route('/<string:eco>', methods=['GET'])
def get_opening(eco):
    """
    获取开局详情
    ---
    tags:
      - 开局管理
    parameters:
      - name: eco
        in: path
        type: string
        required: true
        description: ECO代码
    responses:
      200:
        description: 开局详情(含示例棋谱)
      404:
        description: 开局不存在
    """
    eco = eco.upper()

    opening = Opening.query.filter(Opening.eco_code == eco).first()
    result = None

    if opening:
        result = opening.to_dict()
        recognizer = _get_recognizer()
        eco_info = recognizer.get_eco_info(eco)
        if 'error' not in eco_info:
            result['recognizer_info'] = eco_info
    else:
        recognizer = _get_recognizer()
        eco_info = recognizer.get_eco_info(eco)
        if 'error' in eco_info:
            return jsonify({'error': f'Opening {eco} not found'}), 404
        result = eco_info

    example_games = Game.query.filter(
        Game.eco_code.ilike(f'{eco}%')
    ).order_by(Game.created_at.desc()).limit(6).all()

    result['example_games'] = [{
        'id': g.id,
        'white_player_name': g.white_player.name if g.white_player else '',
        'black_player_name': g.black_player.name if g.black_player else '',
        'white_elo': g.white_elo,
        'black_elo': g.black_elo,
        'result': g.result,
        'date': g.date,
        'eco_code': g.eco_code,
        'opening_name': g.opening_name,
    } for g in example_games]

    return jsonify(result)


@openings_bp.route('/identify', methods=['POST'])
def identify_opening():
    """
    识别开局
    ---
    tags:
      - 开局管理
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - moves
          properties:
            moves:
              type: array
              items:
                type: string
              description: 着法列表(SAN格式)
    responses:
      200:
        description: 识别结果(含相似开局)
      400:
        description: 参数错误
    """
    data = request.get_json()
    if not data or 'moves' not in data:
        return jsonify({'error': 'moves field is required'}), 400

    moves = data['moves']
    if not isinstance(moves, list) or len(moves) == 0:
        return jsonify({'error': 'moves must be a non-empty list'}), 400

    recognizer = _get_recognizer()
    result = recognizer.identify_opening(moves)

    similar = recognizer.find_similar_openings(moves, top_k=3)
    result['similar_openings'] = similar

    return jsonify(result)


@openings_bp.route('/tree', methods=['GET'])
def get_opening_tree():
    """
    获取开局树
    ---
    tags:
      - 开局管理
    responses:
      200:
        description: 开局分类树结构
    """
    recognizer = _get_recognizer()
    tree = recognizer.get_opening_tree()

    db_openings = Opening.query.all()
    db_tree = {}
    for opening in db_openings:
        cat = opening.category
        if cat not in db_tree:
            db_tree[cat] = []
        db_tree[cat].append(opening.to_dict())

    for cat, items in db_tree.items():
        if cat in tree:
            tree[cat]['db_openings'] = items

    return jsonify(tree)
