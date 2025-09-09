"""
認証関連ルート
"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from . import auth
from .utils import check_login_attempts, record_login_attempt, is_safe_url, generate_csrf_token, validate_csrf_token, login_required
from app.models import User, LoginSession
from app import db
from datetime import datetime, timedelta


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン処理"""
    if request.method == 'GET':
        # すでにログイン済みの場合はリダイレクト
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                if user.is_admin:
                    return redirect(url_for('admin.dashboard'))
                else:
                    return redirect(url_for('main.chat'))
        
        return render_template('auth/login.html', 
                             csrf_token=generate_csrf_token())
    
    # POST リクエスト処理
    try:
        # CSRF トークン検証（一時的に無効化）
        # csrf_token = request.form.get('csrf_token')
        # if not validate_csrf_token(csrf_token):
        #     flash('不正なリクエストです。', 'error')
        #     return redirect(url_for('auth.login'))
        
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password', '')
        
        if not user_id or not password:
            flash('ユーザーIDとパスワードを入力してください。', 'error')
            return redirect(url_for('auth.login'))
        
        # ユーザー検索
        user = User.query.filter_by(identifier=user_id).first()
        
        if not user:
            flash('ユーザーIDまたはパスワードが正しくありません。', 'error')
            return redirect(url_for('auth.login'))
        
        # アカウントロック確認
        if not check_login_attempts(user):
            flash('アカウントがロックされています。管理者にお問い合わせください。', 'error')
            return redirect(url_for('auth.login'))
        
        # パスワード確認
        if not user.check_password(password):
            record_login_attempt(user, success=False)
            flash('ユーザーIDまたはパスワードが正しくありません。', 'error')
            return redirect(url_for('auth.login'))
        
        # ログイン成功
        record_login_attempt(user, success=True)
        
        # シンプルなセッション作成
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        
        print(f"Login successful: user_id={user.id}, is_admin={user.is_admin}")
        print(f"Session after login: {dict(session)}")
        
        # リダイレクト先決定
        next_page = request.form.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.chat'))
            
    except Exception as e:
        print(f"ログインエラー: {e}")
        flash('ログイン処理でエラーが発生しました。', 'error')
        return redirect(url_for('auth.login'))


@auth.route('/logout')
def logout():
    """ログアウト処理"""
    try:
        # セッション無効化
        if 'session_id' in session:
            login_session = LoginSession.query.filter_by(
                session_id=session['session_id']
            ).first()
            if login_session:
                login_session.deactivate()
        
        # セッションクリア
        session.clear()
        flash('ログアウトしました。', 'success')
        
    except Exception as e:
        print(f"ログアウトエラー: {e}")
    
    return redirect(url_for('auth.login'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """パスワード変更"""
    user = User.query.get(session['user_id'])
    
    if request.method == 'GET':
        return render_template('auth/change_password.html', 
                             user=user,
                             csrf_token=generate_csrf_token())
    
    try:
        # CSRF トークン検証（一時的に無効化）
        # csrf_token = request.form.get('csrf_token')
        # if not validate_csrf_token(csrf_token):
        #     flash('不正なリクエストです。', 'error')
        #     return redirect(url_for('auth.change_password'))
        
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # バリデーション
        if not current_password or not new_password or not confirm_password:
            flash('すべての項目を入力してください。', 'error')
            return redirect(url_for('auth.change_password'))
        
        if not user.check_password(current_password):
            flash('現在のパスワードが正しくありません。', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('新しいパスワードが一致しません。', 'error')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 6:
            flash('パスワードは6文字以上で入力してください。', 'error')
            return redirect(url_for('auth.change_password'))
        
        # パスワード更新
        user.set_password(new_password)
        user.save()
        
        flash('パスワードを変更しました。', 'success')
        
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.chat'))
            
    except Exception as e:
        print(f"パスワード変更エラー: {e}")
        flash('パスワード変更でエラーが発生しました。', 'error')
        return redirect(url_for('auth.change_password'))


@auth.route('/check-session')
@login_required
def check_session():
    """セッション有効性確認API"""
    try:
        user = User.query.get(session['user_id'])
        login_session = LoginSession.query.filter_by(
            session_id=session.get('session_id')
        ).first()
        
        if not login_session or not login_session.is_active:
            return jsonify({'valid': False, 'message': 'セッションが無効です'})
        
        if login_session.is_expired():
            login_session.deactivate()
            return jsonify({'valid': False, 'message': 'セッションが期限切れです'})
        
        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'user_id': user.user_id,
                'display_name': user.display_name,
                'is_admin': user.is_admin
            }
        })
        
    except Exception as e:
        print(f"セッション確認エラー: {e}")
        return jsonify({'valid': False, 'message': 'エラーが発生しました'})