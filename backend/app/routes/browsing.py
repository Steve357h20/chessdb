import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.browsing_history import BrowsingHistory
from app.models.game import Game

logger = logging.getLogger(__name__)

browsing_bp = Blueprint('browsing', __name__)


@browsing_bp.route('', methods=['GET'])
@jwt_required()
def get_browsing_history():
    """
    获取浏览历史
    ---
    tags:
      - 浏览历史
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
        description: 浏览历史列表
    """
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)

    pagination = BrowsingHistory.query.filter_by(user_id=user_id).order_by(
        BrowsingHistory.viewed_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for bh in pagination.items:
        d = bh.to_dict()
        if bh.game:
            game_dict = bh.game.to_dict()
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


@browsing_bp.route('', methods=['POST'])
@jwt_required()
def record_browsing():
    """
    记录浏览历史
    ---
    tags:
      - 浏览历史
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
    responses:
      201:
        description: 记录成功
      400:
        description: 参数错误
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data or 'game_id' not in data:
        return jsonify({'error': 'game_id is required'}), 400

    game_id = data['game_id']
    game = Game.query.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    existing = BrowsingHistory.query.filter_by(user_id=user_id, game_id=game_id).first()
    if existing:
        existing.viewed_at = db.func.now()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Update browsing error: %s", e)
            return jsonify({'error': 'Failed to update'}), 500
        return jsonify(existing.to_dict())

    bh = BrowsingHistory(user_id=user_id, game_id=game_id)
    try:
        db.session.add(bh)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Record browsing error: %s", e)
        return jsonify({'error': 'Failed to record'}), 500

    return jsonify(bh.to_dict()), 201


@browsing_bp.route('/<int:game_id>', methods=['DELETE'])
@jwt_required()
def delete_browsing(game_id):
    """
    删除浏览记录
    ---
    tags:
      - 浏览历史
    security:
      - Bearer: []
    parameters:
      - name: game_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 删除成功
      404:
        description: 记录不存在
    """
    user_id = int(get_jwt_identity())
    bh = BrowsingHistory.query.filter_by(user_id=user_id, game_id=game_id).first()
    if not bh:
        return jsonify({'error': 'Browsing history not found'}), 404

    try:
        db.session.delete(bh)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Delete browsing error: %s", e)
        return jsonify({'error': 'Failed to delete'}), 500

    return jsonify({'message': 'Deleted'})


@browsing_bp.route('/clear', methods=['POST'])
@jwt_required()
def clear_browsing():
    """
    清空浏览历史
    ---
    tags:
      - 浏览历史
    security:
      - Bearer: []
    responses:
      200:
        description: 清空成功
    """
    user_id = int(get_jwt_identity())
    try:
        BrowsingHistory.query.filter_by(user_id=user_id).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Clear browsing error: %s", e)
        return jsonify({'error': 'Failed to clear'}), 500

    return jsonify({'message': 'Cleared'})
