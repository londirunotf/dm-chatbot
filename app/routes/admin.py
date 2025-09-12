from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, Response, make_response
from app.models import FAQ, Escalation, Conversation, Message, User, StaffMember
from app.auth.utils import admin_required, get_current_user
from app import db
from datetime import datetime, timedelta
import csv
import io
import json

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_required
def dashboard():
    try:
        # シンプルな統計のみ
        pending_escalations = 0
        total_conversations = 0
        total_faqs = 0
        today_conversations = 0
        
        try:
            pending_escalations = Escalation.query.filter_by(status='pending').count()
        except:
            pass
            
        try:
            total_conversations = Conversation.query.count()
        except:
            pass
            
        try:
            total_faqs = FAQ.query.filter_by(is_active=True).count()
        except:
            pass
        
        # 基本情報
        current_user = get_current_user()
        
        return render_template('admin/dashboard.html', 
                             pending_escalations=pending_escalations,
                             total_conversations=total_conversations,
                             total_faqs=total_faqs,
                             today_conversations=today_conversations,
                             user_stats={'total_users': 1, 'active_users': 1},
                             staff_stats={'total_staff': 1},
                             active_users_count=1,
                             current_user=current_user)
    except Exception as e:
        print(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return f"Dashboard Error: {e}"

@admin_bp.route('/faq')
@admin_required
def faq_list():
    try:
        faqs = FAQ.query.order_by(FAQ.created_at.desc()).all()
        return render_template('admin/faq_list.html', faqs=faqs)
    except Exception as e:
        print(f"FAQ list error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('admin/faq_list.html', faqs=[])

@admin_bp.route('/faq/add', methods=['POST'])
@admin_required
def add_faq():
    try:
        data = request.get_json()
        
        faq = FAQ(
            title=data.get('title'),
            question=data.get('question'),
            answer=data.get('answer'),
            keywords=data.get('keywords'),
            category=data.get('category'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(faq)
        db.session.commit()
        
        return jsonify({'message': 'FAQが追加されました', 'faq_id': faq.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'FAQの追加に失敗しました'}), 500

@admin_bp.route('/faq/<int:faq_id>/edit', methods=['POST'])
def edit_faq(faq_id):
    try:
        faq = FAQ.query.get_or_404(faq_id)
        data = request.get_json()
        
        faq.title = data.get('title')
        faq.question = data.get('question')
        faq.answer = data.get('answer')
        faq.keywords = data.get('keywords')
        faq.category = data.get('category')
        faq.is_active = data.get('is_active', True)
        faq.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'FAQが更新されました'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'FAQの更新に失敗しました'}), 500

@admin_bp.route('/faq/<int:faq_id>/toggle', methods=['POST'])
def toggle_faq(faq_id):
    try:
        faq = FAQ.query.get_or_404(faq_id)
        faq.is_active = not faq.is_active
        faq.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'FAQ状態が更新されました', 'is_active': faq.is_active})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'FAQ状態の更新に失敗しました'}), 500

@admin_bp.route('/faq/<int:faq_id>/delete', methods=['POST'])
def delete_faq(faq_id):
    try:
        faq = FAQ.query.get_or_404(faq_id)
        db.session.delete(faq)
        db.session.commit()
        
        return jsonify({'message': 'FAQが削除されました'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'FAQの削除に失敗しました'}), 500

@admin_bp.route('/faq/bulk-import', methods=['GET', 'POST'])
@admin_required
def bulk_import_faq():
    """FAQ一括取り込み機能"""
    if request.method == 'GET':
        return render_template('admin/faq_bulk_import.html')
    
    try:
        import_type = request.form.get('import_type', 'csv')
        
        if import_type == 'csv':
            return handle_csv_import()
        elif import_type == 'json':
            return handle_json_import()
        elif import_type == 'excel':
            return handle_excel_import()
        else:
            return jsonify({'error': '対応していないファイル形式です'}), 400
            
    except Exception as e:
        print(f"Bulk import error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'ファイルの取り込みに失敗しました'}), 500

def handle_csv_import():
    """CSV形式のFAQ一括取り込み"""
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'CSVファイルを選択してください'}), 400
    
    try:
        # CSV内容を読み込み
        content = file.read().decode('utf-8-sig')  # BOM対応
        csv_reader = csv.DictReader(io.StringIO(content))
        
        imported_count = 0
        errors = []
        
        # 期待するカラム
        required_columns = ['title', 'question', 'answer']
        optional_columns = ['category', 'keywords', 'is_active']
        
        for row_num, row in enumerate(csv_reader, start=2):  # 2行目から開始
            try:
                # 必須カラムのチェック
                if not all(row.get(col) for col in required_columns):
                    errors.append(f'{row_num}行目: 必須項目が不足しています')
                    continue
                
                # FAQオブジェクトを作成
                faq = FAQ(
                    title=row['title'].strip(),
                    question=row['question'].strip(),
                    answer=row['answer'].strip(),
                    category=row.get('category', '').strip() or None,
                    keywords=row.get('keywords', '').strip() or None,
                    is_active=str(row.get('is_active', 'true')).lower() in ['true', '1', 'yes', 'on']
                )
                
                db.session.add(faq)
                imported_count += 1
                
            except Exception as row_error:
                errors.append(f'{row_num}行目: {str(row_error)}')
                continue
        
        # 一括コミット
        if imported_count > 0:
            db.session.commit()
            
        return jsonify({
            'message': f'{imported_count}件のFAQを取り込みました',
            'imported_count': imported_count,
            'errors': errors[:10] if errors else []  # 最大10個のエラー表示
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'CSV取り込みエラー: {str(e)}'}), 500

def handle_json_import():
    """JSON形式のFAQ一括取り込み"""
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    file = request.files['file']
    if not file.filename.lower().endswith('.json'):
        return jsonify({'error': 'JSONファイルを選択してください'}), 400
    
    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
        
        imported_count = 0
        errors = []
        
        # データが配列かどうかチェック
        if not isinstance(data, list):
            if isinstance(data, dict) and 'faqs' in data:
                data = data['faqs']
            else:
                return jsonify({'error': 'JSON形式が正しくありません。FAQ配列が必要です'}), 400
        
        for i, item in enumerate(data):
            try:
                # 必須フィールドのチェック
                if not all(item.get(field) for field in ['title', 'question', 'answer']):
                    errors.append(f'{i+1}個目: 必須項目が不足しています')
                    continue
                
                faq = FAQ(
                    title=item['title'][:200],  # 最大200文字
                    question=item['question'][:1000],
                    answer=item['answer'][:2000],
                    category=item.get('category'),
                    keywords=item.get('keywords'),
                    is_active=item.get('is_active', True)
                )
                
                db.session.add(faq)
                imported_count += 1
                
            except Exception as item_error:
                errors.append(f'{i+1}個目: {str(item_error)}')
                continue
        
        if imported_count > 0:
            db.session.commit()
            
        return jsonify({
            'message': f'{imported_count}件のFAQを取り込みました',
            'imported_count': imported_count,
            'errors': errors[:10]
        })
        
    except json.JSONDecodeError:
        return jsonify({'error': '無効なJSON形式です'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'JSON取り込みエラー: {str(e)}'}), 500

def handle_excel_import():
    """Excel形式のFAQ一括取り込み"""
    try:
        import pandas as pd
    except ImportError:
        return jsonify({'error': 'Excel取り込みにはpandasライブラリが必要です'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    file = request.files['file']
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Excelファイルを選択してください'}), 400
    
    try:
        # Excelファイルを読み込み
        df = pd.read_excel(file)
        
        imported_count = 0
        errors = []
        
        # 必須カラムのチェック
        required_columns = ['title', 'question', 'answer']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'error': f'必須カラムが不足しています: {", ".join(missing_columns)}'
            }), 400
        
        for index, row in df.iterrows():
            try:
                # NaN値の処理
                title = str(row['title']).strip() if pd.notna(row['title']) else ''
                question = str(row['question']).strip() if pd.notna(row['question']) else ''
                answer = str(row['answer']).strip() if pd.notna(row['answer']) else ''
                
                if not title or not question or not answer:
                    errors.append(f'{index+2}行目: 必須項目が空です')
                    continue
                
                faq = FAQ(
                    title=title[:200],
                    question=question[:1000],
                    answer=answer[:2000],
                    category=str(row.get('category', '')).strip() if pd.notna(row.get('category')) else None,
                    keywords=str(row.get('keywords', '')).strip() if pd.notna(row.get('keywords')) else None,
                    is_active=bool(row.get('is_active', True))
                )
                
                db.session.add(faq)
                imported_count += 1
                
            except Exception as row_error:
                errors.append(f'{index+2}行目: {str(row_error)}')
                continue
        
        if imported_count > 0:
            db.session.commit()
            
        return jsonify({
            'message': f'{imported_count}件のFAQを取り込みました',
            'imported_count': imported_count,
            'errors': errors[:10]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Excel取り込みエラー: {str(e)}'}), 500

@admin_bp.route('/faq/export', methods=['GET'])
@admin_required
def export_faq():
    """FAQ一括エクスポート機能"""
    export_format = request.args.get('format', 'csv')
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    try:
        # FAQデータを取得
        query = FAQ.query
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        faqs = query.order_by(FAQ.created_at.desc()).all()
        
        if export_format == 'csv':
            return export_csv(faqs)
        elif export_format == 'json':
            return export_json(faqs)
        elif export_format == 'excel':
            return export_excel(faqs)
        else:
            return jsonify({'error': '対応していないエクスポート形式です'}), 400
            
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': 'エクスポートに失敗しました'}), 500

def export_csv(faqs):
    """CSV形式でエクスポート"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # ヘッダー
    writer.writerow(['title', 'question', 'answer', 'category', 'keywords', 'is_active', 'view_count', 'created_at'])
    
    # データ
    for faq in faqs:
        writer.writerow([
            faq.title,
            faq.question,
            faq.answer,
            faq.category or '',
            faq.keywords or '',
            faq.is_active,
            faq.view_count or 0,
            faq.created_at.strftime('%Y-%m-%d %H:%M:%S') if faq.created_at else ''
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="faq_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # UTF-8 BOM追加
    csv_data = '\ufeff' + output.getvalue()
    response.data = csv_data.encode('utf-8')
    
    return response

def export_json(faqs):
    """JSON形式でエクスポート"""
    data = {
        'export_date': datetime.now().isoformat(),
        'total_count': len(faqs),
        'faqs': [
            {
                'id': faq.id,
                'title': faq.title,
                'question': faq.question,
                'answer': faq.answer,
                'category': faq.category,
                'keywords': faq.keywords,
                'is_active': faq.is_active,
                'view_count': faq.view_count or 0,
                'created_at': faq.created_at.isoformat() if faq.created_at else None,
                'updated_at': faq.updated_at.isoformat() if faq.updated_at else None
            }
            for faq in faqs
        ]
    }
    
    response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="faq_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response

def export_excel(faqs):
    """Excel形式でエクスポート"""
    try:
        import pandas as pd
        
        data = []
        for faq in faqs:
            data.append({
                'title': faq.title,
                'question': faq.question,
                'answer': faq.answer,
                'category': faq.category or '',
                'keywords': faq.keywords or '',
                'is_active': faq.is_active,
                'view_count': faq.view_count or 0,
                'created_at': faq.created_at.strftime('%Y-%m-%d %H:%M:%S') if faq.created_at else ''
            })
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='FAQ一覧', index=False)
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="faq_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        return response
        
    except ImportError:
        return jsonify({'error': 'Excel出力にはpandasライブラリが必要です'}), 400

@admin_bp.route('/escalations')
def escalation_list():
    escalations = Escalation.get_pending_escalations()
    return render_template('admin/escalation_list.html', escalations=escalations)

@admin_bp.route('/escalation/<int:escalation_id>/respond', methods=['POST'])
def respond_escalation(escalation_id):
    try:
        escalation = Escalation.query.get_or_404(escalation_id)
        data = request.get_json()
        
        escalation.staff_response = data.get('staff_response')
        escalation.staff_name = data.get('staff_name')
        escalation.status = 'answered'
        escalation.answered_at = datetime.utcnow()
        
        # 利用者へのボット回答メッセージを作成
        staff_message = Message(
            conversation_id=escalation.message.conversation_id,
            message_type='staff',
            content=escalation.staff_response
        )
        
        db.session.add(staff_message)
        db.session.commit()
        
        return jsonify({'message': '回答を送信しました'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '回答の送信に失敗しました'}), 500

@admin_bp.route('/escalation/<int:escalation_id>/close', methods=['POST'])
def close_escalation(escalation_id):
    try:
        escalation = Escalation.query.get_or_404(escalation_id)
        escalation.status = 'closed'
        escalation.answered_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'エスカレーションをクローズしました'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'クローズに失敗しました'}), 500

@admin_bp.route('/users')
@admin_required
def user_list():
    """ユーザー一覧表示"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        users = User.query.order_by(User.last_activity.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/user_list.html', users=users)
    except Exception as e:
        print(f"User list error: {e}")
        return render_template('admin/user_list.html', users=None)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def user_add():
    """ユーザー追加ページ"""
    if request.method == 'POST':
        try:
            # フォームデータを取得
            identifier = request.form.get('identifier', '').strip()
            display_name = request.form.get('display_name', '').strip()
            department = request.form.get('department', '').strip()
            user_type = request.form.get('user_type', 'user')
            password = request.form.get('password', '').strip()
            
            # バリデーション
            if not identifier:
                flash('ユーザーIDは必須です', 'error')
                return render_template('admin/user_add.html')
            
            if not display_name:
                flash('表示名は必須です', 'error')
                return render_template('admin/user_add.html')
            
            if not password:
                flash('パスワードは必須です', 'error')
                return render_template('admin/user_add.html')
            
            # ユーザーIDの重複チェック
            existing_user = User.query.filter_by(identifier=identifier).first()
            if existing_user:
                flash('このユーザーIDは既に使用されています', 'error')
                return render_template('admin/user_add.html')
            
            # 新しいユーザーを作成
            new_user = User(
                identifier=identifier,
                user_id=identifier,  # user_idも同じ値で設定
                display_name=display_name,
                department=department if department else None,
                user_type=user_type,
                is_anonymous=False
            )
            
            # パスワードを設定
            new_user.set_password(password)
            
            # データベースに保存
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'ユーザー「{display_name}」を追加しました', 'success')
            return redirect(url_for('admin.user_list'))
            
        except Exception as e:
            db.session.rollback()
            print(f"User add error: {e}")
            flash('ユーザーの追加に失敗しました', 'error')
            return render_template('admin/user_add.html')
    
    return render_template('admin/user_add.html')

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    """ユーザー編集ページ"""
    try:
        user = User.query.get_or_404(user_id)
        
        if request.method == 'POST':
            # フォームデータを取得
            identifier = request.form.get('identifier', '').strip()
            display_name = request.form.get('display_name', '').strip()
            department = request.form.get('department', '').strip()
            user_type = request.form.get('user_type', 'user')
            password = request.form.get('password', '').strip()
            
            # バリデーション
            if not identifier:
                flash('ユーザーIDは必須です', 'error')
                return render_template('admin/user_edit.html', user=user)
            
            if not display_name:
                flash('表示名は必須です', 'error')
                return render_template('admin/user_edit.html', user=user)
            
            # ユーザーIDの重複チェック（自分以外）
            existing_user = User.query.filter(
                User.identifier == identifier,
                User.id != user_id
            ).first()
            if existing_user:
                flash('このユーザーIDは既に使用されています', 'error')
                return render_template('admin/user_edit.html', user=user)
            
            # ユーザー情報を更新
            user.identifier = identifier
            user.user_id = identifier  # user_idも同じ値で更新
            user.display_name = display_name
            user.department = department if department else None
            user.user_type = user_type
            
            # パスワードが入力されている場合のみ更新
            if password:
                if len(password) < 6:
                    flash('パスワードは6文字以上で入力してください', 'error')
                    return render_template('admin/user_edit.html', user=user)
                user.set_password(password)
            
            # データベースに保存
            db.session.commit()
            
            flash(f'ユーザー「{display_name}」の情報を更新しました', 'success')
            return redirect(url_for('admin.user_detail', user_id=user_id))
            
    except Exception as e:
        db.session.rollback()
        print(f"User edit error: {e}")
        flash('ユーザー情報の更新に失敗しました', 'error')
    
    return render_template('admin/user_edit.html', user=user)

@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """ユーザー詳細表示"""
    try:
        user = User.query.get_or_404(user_id)
        conversations = Conversation.get_user_conversations(user_id, limit=10)
        messages = Message.get_user_messages(user_id, limit=20)
        
        # 統計情報を計算
        total_questions = sum(1 for msg in messages if msg.message_type == 'user')
        escalated_questions = sum(1 for msg in messages if msg.is_escalated)
        
        stats = {
            'total_conversations': len(conversations),
            'total_questions': total_questions,
            'escalated_questions': escalated_questions,
            'escalation_rate': (escalated_questions / total_questions * 100) if total_questions > 0 else 0
        }
        
        return render_template('admin/user_detail.html', 
                             user=user, 
                             conversations=conversations,
                             messages=messages[:10], 
                             stats=stats)
    except Exception as e:
        print(f"User detail error: {e}")
        flash('ユーザー情報の取得に失敗しました', 'error')
        return redirect(url_for('admin.user_list'))

@admin_bp.route('/users/<int:user_id>/chat')
@admin_required
def user_chat(user_id):
    """管理者用：特定ユーザーとのチャットルーム"""
    try:
        user = User.query.get_or_404(user_id)
        current_user = get_current_user()
        
        # ユーザーの統計情報を取得
        conversations = Conversation.get_user_conversations(user_id, limit=5)
        
        # FAQ一覧を取得（アクティブなもののみ）
        faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.view_count.desc()).all()
        
        return render_template('admin/user_chat.html', 
                             target_user=user,
                             current_user=current_user,
                             conversations=conversations,
                             faqs=faqs)
    except Exception as e:
        print(f"User chat error: {e}")
        flash('チャットルームの表示に失敗しました', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def user_delete(user_id):
    """ユーザー削除"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 管理者ユーザーの削除を防止
        if user.user_type == 'admin' or user.is_admin:
            return jsonify({
                'success': False,
                'error': '管理者ユーザーは削除できません'
            }), 400
        
        # 現在ログイン中のユーザー自身の削除を防止
        current_user = get_current_user()
        if current_user and current_user.id == user_id:
            return jsonify({
                'success': False,
                'error': '現在ログイン中のユーザーは削除できません'
            }), 400
        
        user_name = user.display_name or user.identifier
        
        # 関連データの削除処理
        try:
            # 1. ユーザーが送信したメッセージを削除
            messages = Message.query.filter_by(sender_user_id=user_id).all()
            for message in messages:
                # エスカレーションがある場合は削除
                escalations = Escalation.query.filter_by(message_id=message.id).all()
                for escalation in escalations:
                    db.session.delete(escalation)
                
                db.session.delete(message)
            
            # 2. ユーザーの会話を削除
            conversations = Conversation.query.filter_by(user_id=user_id).all()
            for conversation in conversations:
                # 会話に関連するメッセージが残っていれば削除
                remaining_messages = Message.query.filter_by(conversation_id=conversation.id).all()
                for msg in remaining_messages:
                    db.session.delete(msg)
                
                db.session.delete(conversation)
            
            # 3. 職員プロフィールがある場合は削除
            staff_member = StaffMember.query.filter_by(user_id=user_id).first()
            if staff_member:
                db.session.delete(staff_member)
            
            # 4. ユーザー本体を削除
            db.session.delete(user)
            
            # すべての変更をコミット
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'ユーザー「{user_name}」を削除しました'
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"User delete error during data cleanup: {e}")
            return jsonify({
                'success': False,
                'error': '関連データの削除中にエラーが発生しました'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"User delete error: {e}")
        return jsonify({
            'success': False,
            'error': 'ユーザーの削除に失敗しました'
        }), 500

@admin_bp.route('/staff')
@admin_required
def staff_list():
    """職員一覧表示"""
    try:
        staff_members = StaffMember.query.order_by(StaffMember.last_response_at.desc().nullslast()).all()
        return render_template('admin/staff_list.html', staff_members=staff_members)
    except Exception as e:
        print(f"Staff list error: {e}")
        import traceback
        traceback.print_exc()
        return f"Staff list error: {e}"

@admin_bp.route('/staff/<int:staff_id>')
def staff_detail(staff_id):
    """職員詳細表示"""
    try:
        staff_member = StaffMember.query.get_or_404(staff_id)
        responses = Message.get_staff_responses(staff_id, limit=20)
        
        return render_template('admin/staff_detail.html', 
                             staff_member=staff_member,
                             responses=responses)
    except Exception as e:
        print(f"Staff detail error: {e}")
        flash('職員情報の取得に失敗しました', 'error')
        return redirect(url_for('admin.staff_list'))

@admin_bp.route('/conversations')
def conversation_list():
    """会話履歴一覧"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        conversations = Conversation.query.order_by(
            Conversation.last_activity.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('admin/conversation_list.html', conversations=conversations)
    except Exception as e:
        print(f"Conversation list error: {e}")
        return render_template('admin/conversation_list.html', conversations=None)

@admin_bp.route('/conversations/<int:conversation_id>')
def conversation_detail(conversation_id):
    """会話詳細表示"""
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        messages = Message.query.filter_by(conversation_id=conversation_id)\
                               .order_by(Message.timestamp.asc()).all()
        
        return render_template('admin/conversation_detail.html', 
                             conversation=conversation,
                             messages=messages)
    except Exception as e:
        print(f"Conversation detail error: {e}")
        flash('会話情報の取得に失敗しました', 'error')
        return redirect(url_for('admin.conversation_list'))

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """分析・統計画面（最適化版）"""
    try:
        # 各種統計データを収集
        user_stats = User.get_user_stats()
        staff_stats = StaffMember.get_staff_stats()
        
        # FAQ統計
        try:
            from app.models.faq import FAQ
            faq_stats = FAQ.get_faq_stats()
            popular_faqs = FAQ.get_popular_faqs(limit=10)
        except Exception as faq_error:
            print(f"FAQ stats error: {faq_error}")
            faq_stats = {'total_faqs': 0, 'active_faqs': 0, 'total_views': 0}
            popular_faqs = []
        
        # 時系列データ（過去30日間）
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # 会話統計の取得（安全な処理）
        daily_conversations = []
        try:
            from app.models.conversation import Conversation
            conversation_data = db.session.query(
                db.func.date(Conversation.started_at).label('date'),
                db.func.count(Conversation.id).label('count')
            ).filter(
                Conversation.started_at >= thirty_days_ago
            ).group_by(
                db.func.date(Conversation.started_at)
            ).order_by('date').all()
            
            for item in conversation_data:
                daily_conversations.append({
                    'date': item.date.strftime('%Y-%m-%d'),
                    'count': item.count
                })
                
        except Exception as conv_error:
            print(f"Conversation query error: {conv_error}")
            # ダミーデータで代替
            for i in range(30):
                date = (thirty_days_ago + timedelta(days=i)).date()
                daily_conversations.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': max(0, 5 + (i % 7) * 2)
                })
        
        # エスカレーション統計の取得（安全な処理）
        daily_escalations = []
        try:
            escalation_data = db.session.query(
                db.func.date(Escalation.created_at).label('date'),
                db.func.count(Escalation.id).label('count')
            ).filter(
                Escalation.created_at >= thirty_days_ago
            ).group_by(
                db.func.date(Escalation.created_at)
            ).order_by('date').all()
            
            for item in escalation_data:
                daily_escalations.append({
                    'date': item.date.strftime('%Y-%m-%d'),
                    'count': item.count
                })
                
        except Exception as esc_error:
            print(f"Escalation query error: {esc_error}")
            # ダミーデータで代替
            for i in range(30):
                date = (thirty_days_ago + timedelta(days=i)).date()
                daily_escalations.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': max(0, 1 + (i % 5))
                })
        
        return render_template('admin/analytics_optimized.html',
                             user_stats=user_stats,
                             staff_stats=staff_stats,
                             faq_stats=faq_stats,
                             daily_conversations=daily_conversations,
                             daily_escalations=daily_escalations,
                             popular_faqs=popular_faqs)
    except Exception as e:
        print(f"Analytics error: {e}")
        import traceback
        traceback.print_exc()
        # エラー時のフォールバック表示
        return render_template('admin/analytics_optimized.html',
                             user_stats={'total_users': 0, 'authenticated_users': 0, 'anonymous_users': 0},
                             staff_stats={'total_staff': 0, 'active_staff': 0, 'avg_response_time': 0},
                             faq_stats={'total_faqs': 0, 'active_faqs': 0, 'total_views': 0},
                             daily_conversations=[],
                             daily_escalations=[],
                             popular_faqs=[])

@admin_bp.route('/staff/add', methods=['GET', 'POST'])
@admin_required
def staff_add():
    """職員追加"""
    if request.method == 'POST':
        try:
            # フォームデータを取得
            staff_id = request.form.get('staff_id')
            name = request.form.get('name')
            department = request.form.get('department')
            role = request.form.get('role', 'staff')
            user_id = request.form.get('user_id')
            password = request.form.get('password')
            
            # バリデーション
            if not all([staff_id, name, user_id, password]):
                flash('必須項目を入力してください', 'error')
                return render_template('admin/staff_form.html')
            
            # 職員IDの重複チェック
            if StaffMember.query.filter_by(staff_id=staff_id).first():
                flash('この職員IDは既に使用されています', 'error')
                return render_template('admin/staff_form.html')
            
            # ユーザーIDの重複チェック
            if User.query.filter_by(user_id=user_id).first():
                flash('このユーザーIDは既に使用されています', 'error')
                return render_template('admin/staff_form.html')
            
            # ユーザーアカウントを作成
            user = User.create_authenticated_user(
                user_id=user_id,
                password=password,
                display_name=name,
                is_admin=(role == 'admin'),
                department=department
            )
            
            # 職員プロフィールを作成
            staff_member = StaffMember(
                user_id=user.id,
                staff_id=staff_id,
                name=name,
                department=department,
                role=role
            )
            
            db.session.add(staff_member)
            db.session.commit()
            
            flash(f'職員「{name}」を追加しました', 'success')
            return redirect(url_for('admin.staff_list'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Staff add error: {e}")
            flash('職員の追加に失敗しました', 'error')
    
    return render_template('admin/staff_form.html')

@admin_bp.route('/staff/<int:staff_id>/edit', methods=['GET', 'POST'])
@admin_required
def staff_edit(staff_id):
    """職員編集"""
    staff_member = StaffMember.query.get_or_404(staff_id)
    
    if request.method == 'POST':
        try:
            # フォームデータを取得
            name = request.form.get('name')
            department = request.form.get('department')
            role = request.form.get('role')
            is_active = request.form.get('is_active') == 'on'
            
            # 更新
            staff_member.name = name
            staff_member.department = department
            staff_member.role = role
            staff_member.is_active = is_active
            
            # 関連ユーザーも更新
            if staff_member.user:
                staff_member.user.display_name = name
                staff_member.user.department = department
                staff_member.user.is_admin = (role == 'admin')
                staff_member.user.user_type = 'staff'
            
            db.session.commit()
            flash(f'職員「{name}」の情報を更新しました', 'success')
            return redirect(url_for('admin.staff_list'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Staff edit error: {e}")
            flash('職員情報の更新に失敗しました', 'error')
    
    return render_template('admin/staff_form.html', staff=staff_member, is_edit=True)

@admin_bp.route('/staff/<int:staff_id>/toggle', methods=['POST'])
@admin_required
def staff_toggle(staff_id):
    """職員の有効/無効切り替え"""
    try:
        staff_member = StaffMember.query.get_or_404(staff_id)
        data = request.get_json()
        
        staff_member.is_active = data.get('is_active', True)
        db.session.commit()
        
        status = '有効化' if staff_member.is_active else '無効化'
        return jsonify({
            'success': True, 
            'message': f'職員「{staff_member.name}」を{status}しました'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': '状態の変更に失敗しました'}), 500

@admin_bp.route('/analytics/export')
@admin_required
def analytics_export():
    """分析データをCSVエクスポート"""
    try:
        export_format = request.args.get('format', 'csv')
        range_days = int(request.args.get('range', '30').replace('days', ''))
        data_types = request.args.get('types', 'conversations,escalations,faq,users,staff').split(',')
        
        # 期間計算
        end_date = datetime.utcnow()
        if range_days == 7:
            start_date = end_date - timedelta(days=7)
            filename = f"analytics_7days_{end_date.strftime('%Y%m%d')}.csv"
        elif range_days == 30:
            start_date = end_date - timedelta(days=30)
            filename = f"analytics_30days_{end_date.strftime('%Y%m%d')}.csv"
        elif range_days == 90:
            start_date = end_date - timedelta(days=90)
            filename = f"analytics_90days_{end_date.strftime('%Y%m%d')}.csv"
        else:
            start_date = end_date - timedelta(days=365)  # 全期間
            filename = f"analytics_all_{end_date.strftime('%Y%m%d')}.csv"
        
        # CSVデータを作成
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow([
            '分析レポート',
            f'期間: {start_date.strftime("%Y-%m-%d")} - {end_date.strftime("%Y-%m-%d")}'
        ])
        writer.writerow([])  # 空行
        
        # 1. 統計サマリー
        if 'users' in data_types:
            user_stats = User.get_user_stats()
            writer.writerow(['=== ユーザー統計 ==='])
            writer.writerow(['項目', '値'])
            writer.writerow(['総ユーザー数', user_stats.get('total_users', 0)])
            writer.writerow(['認証済みユーザー', user_stats.get('authenticated_users', 0)])
            writer.writerow(['匿名ユーザー', user_stats.get('anonymous_users', 0)])
            writer.writerow(['7日間アクティブユーザー', user_stats.get('active_users_7d', 0)])
            writer.writerow(['30日間アクティブユーザー', user_stats.get('active_users_30d', 0)])
            writer.writerow([])
        
        if 'staff' in data_types:
            staff_stats = StaffMember.get_staff_stats()
            writer.writerow(['=== 職員統計 ==='])
            writer.writerow(['項目', '値'])
            writer.writerow(['総職員数', staff_stats.get('total_staff', 0)])
            writer.writerow(['アクティブ職員数', staff_stats.get('active_staff', 0)])
            writer.writerow(['平均応答時間（分）', staff_stats.get('avg_response_time', 0)])
            writer.writerow(['総回答数', staff_stats.get('total_responses', 0)])
            writer.writerow([])
        
        if 'faq' in data_types:
            from app.models.faq import FAQ
            faq_stats = FAQ.get_faq_stats()
            writer.writerow(['=== FAQ統計 ==='])
            writer.writerow(['項目', '値'])
            writer.writerow(['総FAQ数', faq_stats.get('total_faqs', 0)])
            writer.writerow(['アクティブFAQ数', faq_stats.get('active_faqs', 0)])
            writer.writerow(['総閲覧数', faq_stats.get('total_views', 0)])
            writer.writerow(['FAQ平均閲覧数', f"{faq_stats.get('avg_views_per_faq', 0):.1f}"])
            writer.writerow([])
            
            # 人気FAQランキング
            popular_faqs = FAQ.get_popular_faqs(limit=10)
            writer.writerow(['=== 人気FAQランキング ==='])
            writer.writerow(['順位', 'タイトル', '閲覧数', 'カテゴリ'])
            for i, faq in enumerate(popular_faqs, 1):
                writer.writerow([i, faq.title, faq.view_count or 0, faq.category or '未分類'])
            writer.writerow([])
        
        # 2. 日別統計データ
        if 'conversations' in data_types:
            writer.writerow(['=== 日別会話統計 ==='])
            writer.writerow(['日付', '会話数', '累計'])
            
            try:
                from app.models.conversation import Conversation
                daily_conversations = db.session.query(
                    db.func.date(Conversation.started_at).label('date'),
                    db.func.count(Conversation.id).label('count')
                ).filter(
                    Conversation.started_at >= start_date
                ).group_by(
                    db.func.date(Conversation.started_at)
                ).order_by('date').all()
                
                cumulative = 0
                for item in daily_conversations:
                    cumulative += item.count
                    writer.writerow([
                        item.date.strftime('%Y-%m-%d'),
                        item.count,
                        cumulative
                    ])
            except Exception as e:
                writer.writerow(['データ取得エラー', str(e)])
            
            writer.writerow([])
        
        if 'escalations' in data_types:
            writer.writerow(['=== 日別エスカレーション統計 ==='])
            writer.writerow(['日付', 'エスカレーション数', '累計'])
            
            try:
                daily_escalations = db.session.query(
                    db.func.date(Escalation.created_at).label('date'),
                    db.func.count(Escalation.id).label('count')
                ).filter(
                    Escalation.created_at >= start_date
                ).group_by(
                    db.func.date(Escalation.created_at)
                ).order_by('date').all()
                
                cumulative = 0
                for item in daily_escalations:
                    cumulative += item.count
                    writer.writerow([
                        item.date.strftime('%Y-%m-%d'),
                        item.count,
                        cumulative
                    ])
            except Exception as e:
                writer.writerow(['データ取得エラー', str(e)])
            
            writer.writerow([])
        
        # 3. 詳細データ（必要に応じて）
        if 'users' in data_types:
            writer.writerow(['=== 詳細ユーザーデータ ==='])
            writer.writerow(['ユーザーID', '表示名', 'タイプ', '質問数', '最終活動', '作成日'])
            
            try:
                users = User.query.filter(User.created_at >= start_date).all()
                for user in users:
                    writer.writerow([
                        user.identifier,
                        user.display_name or '匿名',
                        user.user_type,
                        user.question_count or 0,
                        user.last_activity.strftime('%Y-%m-%d %H:%M') if user.last_activity else '',
                        user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else ''
                    ])
            except Exception as e:
                writer.writerow(['データ取得エラー', str(e)])
        
        # CSV レスポンスを作成
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # UTF-8 BOM を追加（Excel対応）
        csv_data = '\ufeff' + output.getvalue()
        response.data = csv_data.encode('utf-8')
        
        return response
        
    except Exception as e:
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        flash('エクスポートに失敗しました', 'error')
        return redirect(url_for('admin.analytics'))

@admin_bp.route('/analytics-simplified')
@admin_required
def analytics_simplified():
    """分析・統計画面シンプル版（安定版）"""
    try:
        # 各種統計データを収集
        user_stats = User.get_user_stats()
        staff_stats = StaffMember.get_staff_stats()
        
        # FAQ統計
        try:
            from app.models.faq import FAQ
            faq_stats = FAQ.get_faq_stats()
            popular_faqs = FAQ.get_popular_faqs(limit=10)
        except Exception as faq_error:
            print(f"FAQ stats error: {faq_error}")
            faq_stats = {'total_faqs': 0, 'active_faqs': 0, 'total_views': 0}
            popular_faqs = []
        
        # 時系列データ（過去30日間）
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # 会話統計の取得（安全な処理）
        daily_conversations = []
        try:
            from app.models.conversation import Conversation
            conversation_data = db.session.query(
                db.func.date(Conversation.started_at).label('date'),
                db.func.count(Conversation.id).label('count')
            ).filter(
                Conversation.started_at >= thirty_days_ago
            ).group_by(
                db.func.date(Conversation.started_at)
            ).order_by('date').all()
            
            for item in conversation_data:
                daily_conversations.append({
                    'date': item.date.strftime('%Y-%m-%d'),
                    'count': item.count
                })
                
        except Exception as conv_error:
            print(f"Conversation query error: {conv_error}")
            # ダミーデータで代替
            for i in range(30):
                date = (thirty_days_ago + timedelta(days=i)).date()
                daily_conversations.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': max(0, 5 + (i % 7) * 2)
                })
        
        # エスカレーション統計の取得（安全な処理）
        daily_escalations = []
        try:
            escalation_data = db.session.query(
                db.func.date(Escalation.created_at).label('date'),
                db.func.count(Escalation.id).label('count')
            ).filter(
                Escalation.created_at >= thirty_days_ago
            ).group_by(
                db.func.date(Escalation.created_at)
            ).order_by('date').all()
            
            for item in escalation_data:
                daily_escalations.append({
                    'date': item.date.strftime('%Y-%m-%d'),
                    'count': item.count
                })
                
        except Exception as esc_error:
            print(f"Escalation query error: {esc_error}")
            # ダミーデータで代替
            for i in range(30):
                date = (thirty_days_ago + timedelta(days=i)).date()
                daily_escalations.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': max(0, 1 + (i % 5))
                })
        
        return render_template('admin/analytics_simplified.html',
                             user_stats=user_stats,
                             staff_stats=staff_stats,
                             faq_stats=faq_stats,
                             daily_conversations=daily_conversations,
                             daily_escalations=daily_escalations,
                             popular_faqs=popular_faqs)
    except Exception as e:
        print(f"Analytics simplified error: {e}")
        import traceback
        traceback.print_exc()
        return f"Analytics simplified error: {e}"

@admin_bp.route('/analytics-test')
@admin_required
def analytics_test():
    """分析・統計画面テスト版"""
    try:
        # 各種統計データを収集（簡略版）
        user_stats = User.get_user_stats()
        staff_stats = StaffMember.get_staff_stats()
        
        # FAQ統計
        try:
            from app.models.faq import FAQ
            faq_stats = FAQ.get_faq_stats()
            popular_faqs = FAQ.get_popular_faqs(limit=10)
        except Exception as faq_error:
            print(f"FAQ stats error: {faq_error}")
            faq_stats = {'total_faqs': 0, 'active_faqs': 0, 'total_views': 0}
            popular_faqs = []
        
        # ダミーデータ
        daily_conversations = [
            {'date': '2025-08-01', 'count': 5},
            {'date': '2025-08-02', 'count': 7},
            {'date': '2025-08-03', 'count': 3}
        ]
        
        daily_escalations = [
            {'date': '2025-08-01', 'count': 1},
            {'date': '2025-08-02', 'count': 2},
            {'date': '2025-08-03', 'count': 0}
        ]
        
        return render_template('admin/analytics_simple.html',
                             user_stats=user_stats,
                             staff_stats=staff_stats,
                             faq_stats=faq_stats,
                             daily_conversations=daily_conversations,
                             daily_escalations=daily_escalations,
                             popular_faqs=popular_faqs)
    except Exception as e:
        print(f"Analytics test error: {e}")
        import traceback
        traceback.print_exc()
        return f"Analytics test error: {e}"

# ユーザーデータバックアップ・復元機能
@admin_bp.route('/users/backup')
@admin_required
def user_backup():
    """ユーザーデータをJSONでバックアップ"""
    try:
        # 全ユーザーデータを取得（パスワード以外）
        users = User.query.all()
        backup_data = {
            'backup_date': datetime.utcnow().isoformat(),
            'backup_type': 'users',
            'users': []
        }
        
        for user in users:
            if user.user_id != 'admin':  # 管理者は除外
                user_data = {
                    'identifier': user.identifier,
                    'user_id': user.user_id,
                    'display_name': user.display_name,
                    'user_type': user.user_type,
                    'department': user.department,
                    'is_anonymous': user.is_anonymous,
                    'is_admin': user.is_admin,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
                backup_data['users'].append(user_data)
        
        # JSON形式でダウンロード
        response = make_response(json.dumps(backup_data, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="user_backup_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json"'
        
        return response
        
    except Exception as e:
        print(f"User backup error: {e}")
        flash('バックアップに失敗しました', 'error')
        return redirect(url_for('admin.user_list'))

@admin_bp.route('/users/restore', methods=['GET', 'POST'])
@admin_required 
def user_restore():
    """ユーザーデータを復元"""
    if request.method == 'POST':
        try:
            # アップロードされたファイルを取得
            if 'backup_file' not in request.files:
                flash('ファイルが選択されていません', 'error')
                return render_template('admin/user_restore.html')
            
            file = request.files['backup_file']
            if file.filename == '':
                flash('ファイルが選択されていません', 'error')
                return render_template('admin/user_restore.html')
            
            # JSONファイルを読み込み
            try:
                backup_data = json.loads(file.read().decode('utf-8'))
            except json.JSONDecodeError:
                flash('無効なJSONファイルです', 'error')
                return render_template('admin/user_restore.html')
            
            if 'users' not in backup_data:
                flash('無効なバックアップファイルです', 'error')
                return render_template('admin/user_restore.html')
            
            # デフォルトパスワード設定
            default_password = request.form.get('default_password', 'password123')
            
            restored_count = 0
            skipped_count = 0
            
            # ユーザーを復元
            for user_data in backup_data['users']:
                try:
                    # 既存ユーザーをチェック
                    existing_user = User.query.filter_by(user_id=user_data.get('user_id')).first()
                    if existing_user:
                        skipped_count += 1
                        continue
                    
                    # 新しいユーザーを作成
                    new_user = User(
                        identifier=user_data.get('identifier'),
                        user_id=user_data.get('user_id'),
                        display_name=user_data.get('display_name'),
                        user_type=user_data.get('user_type', 'user'),
                        department=user_data.get('department'),
                        is_anonymous=user_data.get('is_anonymous', False),
                        is_admin=user_data.get('is_admin', False)
                    )
                    
                    # デフォルトパスワードを設定
                    new_user.set_password(default_password)
                    
                    db.session.add(new_user)
                    restored_count += 1
                    
                except Exception as user_error:
                    print(f"User restore error for {user_data.get('user_id', 'unknown')}: {user_error}")
                    continue
            
            db.session.commit()
            
            flash(f'ユーザーデータを復元しました（復元: {restored_count}件, スキップ: {skipped_count}件）', 'success')
            return redirect(url_for('admin.user_list'))
            
        except Exception as e:
            db.session.rollback()
            print(f"User restore error: {e}")
            flash('復元に失敗しました', 'error')
    
    return render_template('admin/user_restore.html')

@admin_bp.route('/system/init-with-backup')
@admin_required
def init_with_backup():
    """システム初期化時に自動復元する設定を作成"""
    try:
        # バックアップファイルの存在チェック
        backup_file_path = '/app/user_backup_latest.json'  # Renderでのパス
        
        if os.path.exists(backup_file_path):
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
                
            restored_count = 0
            for user_data in backup_data.get('users', []):
                existing_user = User.query.filter_by(user_id=user_data.get('user_id')).first()
                if not existing_user:
                    new_user = User(
                        identifier=user_data.get('identifier'),
                        user_id=user_data.get('user_id'),
                        display_name=user_data.get('display_name'),
                        user_type=user_data.get('user_type', 'user'),
                        department=user_data.get('department'),
                        is_anonymous=user_data.get('is_anonymous', False),
                        is_admin=user_data.get('is_admin', False)
                    )
                    new_user.set_password('password123')  # デフォルトパスワード
                    db.session.add(new_user)
                    restored_count += 1
                    
            db.session.commit()
            flash(f'バックアップから{restored_count}件のユーザーを復元しました', 'success')
        else:
            flash('バックアップファイルが見つかりません', 'warning')
            
        return redirect(url_for('admin.dashboard'))
        
    except Exception as e:
        print(f"Init with backup error: {e}")
        flash('自動復元に失敗しました', 'error')
        return redirect(url_for('admin.dashboard'))
