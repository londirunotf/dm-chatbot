from app import create_app
import os

app = create_app()

# データベース初期化と管理者アカウント作成
def init_database():
    with app.app_context():
        from app import db
        from app.models.user import User
        from app.models.faq import FAQ
        from app.models.conversation import Conversation
        from app.models.escalation import Escalation

        try:
            # データベーステーブルを作成
            db.create_all()
            print("データベーステーブルを作成しました")

            # 管理者が存在するかチェック
            admin = User.query.filter_by(user_id='admin').first()
            if not admin:
                # 管理者アカウント作成
                admin_user = User(
                    identifier='admin',
                    user_id='admin',
                    display_name='管理者',
                    user_type='admin',
                    is_anonymous=False,
                    is_admin=True
                )
                admin_user.set_password('123456')
                db.session.add(admin_user)
                db.session.commit()
                print("管理者アカウントを作成しました: admin/123456")
            else:
                print("管理者アカウントは既に存在します")
            
            # バックアップからユーザーデータを自動復元
            try:
                backup_file_path = 'user_backup_latest.json'
                if os.path.exists(backup_file_path):
                    print("バックアップファイルを発見しました。ユーザーデータを復元中...")
                    import json
                    
                    with open(backup_file_path, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    restored_count = 0
                    for user_data in backup_data.get('users', []):
                        # 既存ユーザーをチェック
                        existing_user = User.query.filter_by(user_id=user_data.get('user_id')).first()
                        if not existing_user:
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
                            new_user.set_password('password123')  # デフォルトパスワード
                            db.session.add(new_user)
                            restored_count += 1
                    
                    if restored_count > 0:
                        db.session.commit()
                        print(f"バックアップから{restored_count}件のユーザーを復元しました")
                    else:
                        print("復元対象のユーザーはありませんでした")
                        
            except Exception as backup_error:
                print(f"バックアップ復元エラー: {backup_error}")
                # エラーでも処理を継続

        except Exception as e:
            print(f"データベース初期化エラー: {e}")
            import traceback
            traceback.print_exc()
            try:
                db.session.rollback()
            except:
                pass

if __name__ == '__main__':
    # データベース初期化を常に実行
    init_database()

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)