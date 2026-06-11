import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload

from app import db
from app.models.collection import Collection
from app.models.game import Game

logger = logging.getLogger(__name__)

collections_bp = Blueprint('collections', __name__)


@collections_bp.route('', methods=['GET'])
@jwt_required()
def get_collections():
    """
    获取用户收藏列表
    ---
    tags:
      - 收藏管理
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: 收藏列表
    """
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    pagination = Collection.query.filter_by(user_id=user_id).order_by(
        Collection.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for col in pagination.items:
        d = col.to_dict()
        if col.game:
            game_dict = col.game.to_dict()
            d['white_player_name'] = game_dict.get('white_player_name', '')
            d['black_player_name'] = game_dict.get('black_player_name', '')
            d['result'] = game_dict.get('result', '*')
            d['eco_code'] = game_dict.get('eco_code', '')
            d['opening_name'] = game_dict.get('opening_name', '')
            d['date'] = game_dict.get('date', '')
        items.append(d)

    return jsonify({
        'items': items,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
    })


@collections_bp.route('', methods=['POST'])
@jwt_required()
def add_collection():
    """
    添加收藏
    ---
    tags:
      - 收藏管理
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - game_id
          properties:
            game_id:
              type: integer
            note:
              type: string
    responses:
      201:
        description: 收藏成功
      409:
        description: 已收藏
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or 'game_id' not in data:
        return jsonify({'error': 'game_id is required'}), 400

    game_id = data['game_id']
    game = Game.query.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    existing = Collection.query.filter_by(user_id=user_id, game_id=game_id).first()
    if existing:
        return jsonify({'error': 'Already in collection', 'collection': existing.to_dict()}), 409

    col = Collection(
        user_id=user_id,
        game_id=game_id,
        note=data.get('note', ''),
    )
    try:
        db.session.add(col)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Add collection error: %s", e)
        return jsonify({'error': 'Failed to add'}), 500

    return jsonify(col.to_dict()), 201


@collections_bp.route('/<int:collection_id>', methods=['DELETE'])
@jwt_required()
def remove_collection(collection_id):
    """
    删除收藏
    ---
    tags:
      - 收藏管理
    security:
      - Bearer: []
    parameters:
      - name: collection_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 删除成功
      404:
        description: 收藏不存在
    """
    user_id = int(get_jwt_identity())
    col = Collection.query.filter_by(id=collection_id, user_id=user_id).first()
    if not col:
        return jsonify({'error': 'Collection not found'}), 404

    try:
        db.session.delete(col)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Remove collection error: %s", e)
        return jsonify({'error': 'Failed to remove'}), 500

    return jsonify({'message': 'Removed from collection'})


@collections_bp.route('/check/<int:game_id>', methods=['GET'])
@jwt_required()
def check_collection(game_id):
    """
    检查棋谱是否已收藏
    ---
    tags:
      - 收藏管理
    security:
      - Bearer: []
    parameters:
      - name: game_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 返回是否已收藏
    """
    user_id = int(get_jwt_identity())
    col = Collection.query.filter_by(user_id=user_id, game_id=game_id).first()
    return jsonify({
        'is_collected': col is not None,
        'collection': col.to_dict() if col else None,
    })


@collections_bp.route('/<int:collection_id>', methods=['PUT'])
@jwt_required()
def update_collection_note(collection_id):
    """
    更新收藏备注
    ---
    tags:
      - 收藏管理
    security:
      - Bearer: []
    parameters:
      - name: collection_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            note:
              type: string
    responses:
      200:
        description: 更新成功
      404:
        description: 收藏不存在
    """
    user_id = int(get_jwt_identity())
    col = Collection.query.filter_by(id=collection_id, user_id=user_id).first()
    if not col:
        return jsonify({'error': 'Collection not found'}), 404

    data = request.get_json()
    if data and 'note' in data:
        col.note = data['note']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update'}), 500

    return jsonify(col.to_dict())
