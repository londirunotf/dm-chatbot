from flask import Blueprint, request, jsonify, session
from app.models import FAQ, Conversation, Message, Escalation, User, StaffMember
from app.auth.utils import login_required, admin_required, get_current_user
from app import db
from datetime import datetime
import uuid
import hashlib

api_bp = Blueprint('api', __name__)

@api_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    """プライベートチャット用メッセージ送信API"""
    data = request.get_json()
    message_content = data.get('message', '').strip()
    
    if not message_content:
        return jsonify({'error': 'メッセージが空です'}), 400
    
    try:
        # 現在ログイン中のユーザーを取得
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '認証が必要です'}), 401
        
        # ユーザー固有のセッションIDを使用（一意性を確保）
        user_session_id = f"user_{current_user.id}_main_session"
        
        # そのユーザー専用のメイン会話セッションを取得または作成
        conversation = Conversation.query.filter_by(
            session_id=user_session_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                session_id=user_session_id,
                user_id=current_user.id,
                user_display_name=current_user.display_name
            )
            db.session.add(conversation)
            db.session.flush()
        
        # 最終アクティビティを更新
        conversation.last_activity = datetime.utcnow()
        current_user.update_activity()
        
        # ユーザーの統計を更新
        current_user.increment_question_count()
        
        # ユーザーメッセージを保存
        user_message = Message(
            conversation_id=conversation.id,
            message_type='user',
            content=message_content
        )
        
        # ユーザー情報をメッセージに設定
        user_message.set_sender_from_user(current_user)
        
        db.session.add(user_message)
        db.session.flush()
        
        # FAQ検索
        matching_faqs = FAQ.search(message_content)
        
        if matching_faqs:
            # 最も関連性の高いFAQを選択
            best_faq = matching_faqs[0]
            best_faq.view_count += 1
            
            # ボット回答を保存
            bot_message = Message(
                conversation_id=conversation.id,
                message_type='bot',
                content=best_faq.answer,
                faq_id=best_faq.id
            )
            db.session.add(bot_message)
            
            response = {
                'type': 'faq_answer',
                'message': best_faq.answer,
                'faq_title': best_faq.title,
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            # FAQが見つからない場合はエスカレーション
            user_message.is_escalated = True
            
            escalation = Escalation(message_id=user_message.id)
            db.session.add(escalation)
            
            response = {
                'type': 'escalation',
                'message': 'この質問については職員が確認して回答いたします。しばらくお待ちください。',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        db.session.commit()
        return jsonify(response)
        
    except Exception as e:
        db.session.rollback()
        print(f"Send message error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500

@api_bp.route('/get_messages')
@login_required
def get_messages():
    """ユーザー専用チャットのメッセージ取得"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '認証が必要です', 'messages': []}), 401
        
        # 管理者の場合は、指定されたユーザーのメッセージを取得可能
        target_user_id = current_user.id
        if current_user.is_admin and request.args.get('user_id'):
            target_user_id = int(request.args.get('user_id'))
        
        # そのユーザーの全メッセージを時系列で取得（全会話セッション統合）
        messages = db.session.query(Message)\
                    .join(Conversation, Message.conversation_id == Conversation.id)\
                    .filter(Conversation.user_id == target_user_id)\
                    .order_by(Message.timestamp.asc()).all()
        
        # メイン会話セッションを取得（統合表示用）
        main_session_id = f"user_{target_user_id}_main_session"
        main_conversation = Conversation.query.filter_by(
            session_id=main_session_id,
            user_id=target_user_id
        ).first()
        
        conversation_id = main_conversation.id if main_conversation else None
        
        return jsonify({
            'messages': [msg.to_dict() for msg in messages],
            'conversation_id': conversation_id,
            'user_info': {
                'id': current_user.id,
                'display_name': current_user.display_name,
                'is_admin': current_user.is_admin
            }
        })
    
    except Exception as e:
        print(f"Get messages error: {e}")
        return jsonify({'error': 'メッセージ取得でエラーが発生しました', 'messages': []}), 500

@api_bp.route('/identify-user', methods=['POST'])
def identify_user():
    """ユーザー識別 - 名前と部署を登録"""
    try:
        data = request.get_json()
    except Exception:
        return jsonify({'error': '有効なJSONデータが必要です'}), 400
        
    try:
        if not data or not isinstance(data, dict):
            return jsonify({'error': '有効なJSONデータが必要です'}), 400
        
        display_name = data.get('display_name')
        if display_name is None:
            return jsonify({'error': '名前は必須です'}), 400
        
        if not isinstance(display_name, str):
            return jsonify({'error': '名前は文字列である必要があります'}), 400
            
        display_name = display_name.strip()
        department = data.get('department', '').strip() if isinstance(data.get('department'), str) else ''
        session_id = data.get('session_id', '') if isinstance(data.get('session_id'), str) else ''
        
        if not display_name:
            return jsonify({'error': '名前を入力してください'}), 400
            
        # ユーザーを作成または更新
        user = User.get_or_create_user(
            display_name=display_name,
            user_type='user'
        )
        user.department = department
        
        # セッション情報を更新
        session['user_id'] = user.id
        session['user_display_name'] = display_name
        
        # 既存の会話セッションにユーザー情報を関連付け
        if session_id:
            conversation = Conversation.query.filter_by(session_id=session_id).first()
            if conversation:
                conversation.user_id = user.id
                conversation.user_display_name = display_name
                
                # この会話の既存メッセージにユーザー情報を設定
                for message in conversation.messages:
                    if message.message_type == 'user' and not message.sender_user_id:
                        message.set_sender_from_user(user)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'message': f'こんにちは、{display_name}さん！'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'ユーザー識別中にエラーが発生しました'}), 500

@api_bp.route('/identify-staff', methods=['POST'])
def identify_staff():
    """職員識別 - 管理者向け機能"""
    data = request.get_json()
    staff_id = data.get('staff_id', '').strip()
    name = data.get('name', '').strip()
    department = data.get('department', '').strip()
    session_id = data.get('session_id', '')
    
    if not staff_id or not name:
        return jsonify({'error': '職員IDと名前を入力してください'}), 400
    
    try:
        # ユーザーを作成
        user = User.get_or_create_user(
            identifier=f"staff_{staff_id}",
            display_name=name,
            user_type='staff'
        )
        user.department = department
        user.is_anonymous = False
        
        # 職員情報を作成または更新
        staff_member = StaffMember.query.filter_by(staff_id=staff_id).first()
        if not staff_member:
            staff_member = StaffMember(
                user_id=user.id,
                staff_id=staff_id,
                name=name,
                department=department
            )
            db.session.add(staff_member)
        else:
            staff_member.name = name
            staff_member.department = department
        
        # セッション情報を更新
        session['user_id'] = user.id
        session['staff_id'] = staff_member.id
        session['user_display_name'] = name
        session['user_type'] = 'staff'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'staff': staff_member.to_dict(),
            'message': f'職員として識別されました: {name}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '職員識別中にエラーが発生しました'}), 500

@api_bp.route('/user-stats/<int:user_id>')
def get_user_stats(user_id):
    """ユーザー統計情報を取得"""
    try:
        user = User.query.get_or_404(user_id)
        
        # ユーザーの会話履歴を取得
        conversations = Conversation.get_user_conversations(user_id, limit=50)
        messages = Message.get_user_messages(user_id, limit=100)
        
        # 統計情報を計算
        total_questions = sum(1 for msg in messages if msg.message_type == 'user')
        escalated_questions = sum(1 for msg in messages if msg.is_escalated)
        
        return jsonify({
            'user': user.to_dict(),
            'stats': {
                'total_conversations': len(conversations),
                'total_questions': total_questions,
                'escalated_questions': escalated_questions,
                'escalation_rate': (escalated_questions / total_questions * 100) if total_questions > 0 else 0
            },
            'recent_conversations': [conv.to_dict() for conv in conversations[:5]]
        })
        
    except Exception as e:
        return jsonify({'error': '統計情報の取得に失敗しました'}), 500

@api_bp.route('/staff-stats/<int:staff_id>')
def get_staff_stats(staff_id):
    """職員統計情報を取得"""
    try:
        staff_member = StaffMember.query.get_or_404(staff_id)
        
        # 職員の回答履歴を取得
        responses = Message.get_staff_responses(staff_id, limit=50)
        
        return jsonify({
            'staff': staff_member.to_dict(),
            'stats': {
                'total_responses': len(responses),
                'average_response_time': staff_member.average_response_time,
                'last_response_at': staff_member.last_response_at.isoformat() if staff_member.last_response_at else None
            },
            'recent_responses': [msg.to_dict() for msg in responses[:10]]
        })
        
    except Exception as e:
        return jsonify({'error': '職員統計情報の取得に失敗しました'}), 500

@api_bp.route('/anonymous-hash', methods=['POST'])
def generate_anonymous_hash():
    """匿名ユーザー用のハッシュIDを生成"""
    data = request.get_json()
    session_info = data.get('session_info', '')
    
    # セッション情報をもとにハッシュを生成（個人情報は含まない）
    hash_source = f"{session_info}_{datetime.utcnow().strftime('%Y%m%d')}"
    anonymous_hash = hashlib.md5(hash_source.encode()).hexdigest()[:8]
    
    return jsonify({
        'anonymous_id': f"guest_{anonymous_hash}",
        'display_name': f"ゲスト#{anonymous_hash}"
    })

@api_bp.route('/admin_send_message', methods=['POST'])
@admin_required
def admin_send_message():
    """管理者用メッセージ送信API"""
    data = request.get_json()
    message_content = data.get('message', '').strip()
    target_user_id = data.get('target_user_id')
    
    if not message_content:
        return jsonify({'error': 'メッセージが空です'}), 400
    
    if not target_user_id:
        return jsonify({'error': '対象ユーザーが指定されていません'}), 400
    
    try:
        # 現在の管理者ユーザーを取得
        current_user = get_current_user()
        if not current_user or not current_user.is_admin:
            return jsonify({'error': '管理者権限が必要です'}), 403
        
        # 対象ユーザーを取得
        target_user = User.query.get_or_404(target_user_id)
        
        # 対象ユーザーのメイン会話セッションを取得または作成
        user_session_id = f"user_{target_user_id}_main_session"
        conversation = Conversation.query.filter_by(
            session_id=user_session_id,
            user_id=target_user_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                session_id=user_session_id,
                user_id=target_user_id,
                user_display_name=target_user.display_name
            )
            db.session.add(conversation)
            db.session.flush()
        
        # 最終アクティビティを更新
        conversation.last_activity = datetime.utcnow()
        
        # 管理者の回答メッセージを保存
        staff_message = Message(
            conversation_id=conversation.id,
            message_type='staff',
            content=message_content
        )
        
        # 送信者情報を設定
        staff_message.sender_user_id = current_user.id
        staff_message.sender_name = current_user.display_name or current_user.identifier
        staff_message.sender_type = 'staff'
        
        db.session.add(staff_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '管理者回答を送信しました',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Admin send message error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'エラーが発生しました: {str(e)}'}), 500

@api_bp.route('/get_users')
@admin_required
def get_users():
    """管理者用ユーザー一覧取得API"""
    try:
        # 全ユーザーを取得（メッセージ数と最終活動時刻を含む）
        users = db.session.query(User).order_by(User.last_activity.desc().nullslast()).all()
        
        user_list = []
        for user in users:
            # そのユーザーのメッセージ数を計算
            message_count = db.session.query(Message)\
                .join(Conversation, Message.conversation_id == Conversation.id)\
                .filter(Conversation.user_id == user.id)\
                .filter(Message.message_type == 'user')\
                .count()
            
            user_dict = user.to_dict()
            user_dict['message_count'] = message_count
            user_list.append(user_dict)
        
        return jsonify({
            'success': True,
            'users': user_list,
            'count': len(user_list)
        })
        
    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'error': 'ユーザー一覧の取得に失敗しました', 'users': []}), 500

@api_bp.route('/search-faq', methods=['POST'])
def search_faq():
    """FAQ検索API"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': '検索クエリが空です', 'faqs': []}), 400
        
        # FAQ検索を実行
        matching_faqs = FAQ.search(query)
        
        # 結果を辞書形式に変換
        faq_results = []
        for faq in matching_faqs:
            faq_dict = faq.to_dict()
            faq_results.append(faq_dict)
        
        return jsonify({
            'success': True,
            'query': query,
            'count': len(faq_results),
            'faqs': faq_results
        })
        
    except Exception as e:
        print(f"FAQ search error: {e}")
        return jsonify({'error': 'FAQ検索でエラーが発生しました', 'faqs': []}), 500

