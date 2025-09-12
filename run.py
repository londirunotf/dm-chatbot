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