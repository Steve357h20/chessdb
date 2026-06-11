import logging
import re

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
)

from app import db, limiter
from app.models.user import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """
    用户注册
    ---
    tags:
      - 认证管理
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              minLength: 3
              maxLength: 80
            email:
              type: string
              format: email
            password:
              type: string
              minLength: 6
    responses:
      201:
        description: 注册成功
      400:
        description: 参数错误
      409:
        description: 用户名或邮箱已存在
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email and password are required'}), 400

    if len(username) < 3 or len(username) > 80:
        return jsonify({'error': 'Username must be between 3 and 80 characters'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'error': 'Invalid email format'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 409

    user = User(username=username, email=email)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Registration error: %s", e)
        return jsonify({'error': 'Registration failed'}), 500

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Registration successful',
        'user': user.to_dict(),
        'access_token': access_token,
    }), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    用户登录
    ---
    tags:
      - 认证管理
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: 登录成功，返回JWT令牌
      401:
        description: 用户名或密码错误
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
    })


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    用户登出
    ---
    tags:
      - 认证管理
    security:
      - Bearer: []
    responses:
      200:
        description: 登出成功
    """
    return jsonify({'message': 'Logout successful'})


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    更新用户资料
    ---
    tags:
      - 认证管理
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            username:
              type: string
            email:
              type: string
            old_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: 更新成功
      400:
        description: 参数错误
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'username' in data and data['username']:
        username = data['username'].strip()
        if len(username) < 3 or len(username) > 80:
            return jsonify({'error': 'Username must be between 3 and 80 characters'}), 400
        existing = User.query.filter(User.username == username, User.id != user.id).first()
        if existing:
            return jsonify({'error': 'Username already in use'}), 409
        user.username = username

    if 'email' in data and data['email']:
        email = data['email'].strip()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Invalid email format'}), 400
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            return jsonify({'error': 'Email already in use'}), 409
        user.email = email

    if 'old_password' in data and 'new_password' in data:
        if not user.check_password(data['old_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        if len(data['new_password']) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        user.set_password(data['new_password'])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Profile update error: %s", e)
        return jsonify({'error': 'Update failed'}), 500

    return jsonify({
        'message': 'Profile updated',
        'user': user.to_dict(),
    })


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    获取当前用户资料
    ---
    tags:
      - 认证管理
    security:
      - Bearer: []
    responses:
      200:
        description: 用户资料
      404:
        description: 用户不存在
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    result = user.to_dict()
    collection_count = user.collections.count()
    result['collection_count'] = collection_count

    return jsonify(result)
