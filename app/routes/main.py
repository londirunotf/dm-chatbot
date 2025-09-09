from flask import Blueprint, render_template, session, jsonify, redirect, url_for
from app.models import FAQ, User
from app.auth.utils import login_required, get_current_user
import uuid

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """ルートページ - FAQ一覧付きLINE風チャット"""
    try:
        # セッションIDを生成（存在しない場合）
        if 'session_id' not in session:
            session['session_id'] = uuid.uuid4().hex
        
        # FAQ一覧を取得（アクティブなもののみ）
        faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.view_count.desc()).all()
        
        return render_template('index.html', faqs=faqs)
    except Exception as e:
        print(f"Index route error: {e}")
        # エラー時でも基本画面を表示
        return render_template('index.html', faqs=[])

@main_bp.route('/chat')
@login_required
def chat():
    """ユーザー専用チャット画面"""
    try:
        current_user = get_current_user()
        
        # FAQ一覧を取得（アクティブなもののみ）
        faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.view_count.desc()).all()
        
        return render_template('user/chat.html', faqs=faqs, user=current_user)
    except Exception as e:
        print(f"Chat route error: {e}")
        # エラー時でも基本画面を表示
        return render_template('user/chat.html', faqs=[], user=current_user)


@main_bp.route('/test-faq')
def test_faq():
    """FAQデータのテスト用エンドポイント"""
    try:
        faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.view_count.desc()).all()
        faq_data = [faq.to_dict() for faq in faqs]
        return jsonify({
            'count': len(faqs),
            'faqs': faq_data
        })
    except Exception as e:
        return jsonify({'error': str(e)})