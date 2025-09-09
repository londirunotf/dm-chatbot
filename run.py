from app import create_app
import os

app = create_app()

# 管理者アカウントを自動作成（本番環境用）
def init_admin():
    with app.app_context():
        from app.models.user import User
        from app import db
        
        # 管理者が存在するかチェック
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # 管理者アカウント作成
            admin_user = User(
                username='admin',
                display_name='管理者',
                is_admin=True
            )
            admin_user.set_password('123456')
            db.session.add(admin_user)
            db.session.commit()
            print("管理者アカウントを作成しました")

if __name__ == '__main__':
    # 本番環境でのみ管理者を自動作成
    if os.environ.get('DATABASE_URL'):
        init_admin()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)