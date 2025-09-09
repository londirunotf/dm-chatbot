"""
認証ユーティリティ関数
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request
from app.models import User
from datetime import datetime


def login_required(f):
    """ログイン必須デコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('ログインが必要です。', 'error')
            return redirect(url_for('auth.login'))
        
        # セッション有効性チェック
        user = User.query.get(session['user_id'])
        if not user or user.is_locked:
            session.clear()
            flash('アカウントがロックされています。管理者にお問い合わせください。', 'error')
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理者権限必須デコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"Admin check - Session: {dict(session)}")
        
        if 'user_id' not in session:
            print("Admin check FAILED: No user_id in session")
            flash('ログインが必要です。', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        print(f"Admin check - User found: {user}")
        
        if not user:
            print("Admin check FAILED: User not found")
            flash('ログインが必要です。', 'error')
            return redirect(url_for('auth.login'))
            
        if not user.is_admin:
            print(f"Admin check FAILED: User is not admin (is_admin={user.is_admin})")
            flash('管理者権限が必要です。', 'error')
            return redirect(url_for('main.chat'))
        
        print("Admin check PASSED")
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """現在ログイン中のユーザーを取得"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def check_login_attempts(user):
    """ログイン試行回数をチェック"""
    if user.login_attempts >= 5:
        user.is_locked = True
        user.save()
        return False
    return True


def record_login_attempt(user, success=False):
    """ログイン試行を記録"""
    if success:
        user.login_attempts = 0
        user.last_login = datetime.utcnow()
        user.is_locked = False
    else:
        user.login_attempts = (user.login_attempts or 0) + 1
        if user.login_attempts >= 5:
            user.is_locked = True
    
    user.save()


def is_safe_url(target):
    """リダイレクト先URLの安全性をチェック"""
    return target and target.startswith('/')


def generate_csrf_token():
    """CSRF トークンを生成"""
    import secrets
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']


def validate_csrf_token(token):
    """CSRF トークンを検証"""
    return token and token == session.get('_csrf_token')