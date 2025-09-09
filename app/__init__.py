from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
csrf = CSRFProtect()

def create_app(config=None):
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # データベースファイルの絶対パスを使用
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'chatbot.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Apply test configuration if provided
    if config:
        app.config.update(config)
    
    # セッション設定（開発環境用に修正）
    app.config['SESSION_COOKIE_SECURE'] = False  # HTTPでもセッション有効
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 28800  # 8時間
    
    # Initialize extensions
    db.init_app(app)
    # 一時的にCSRF保護を無効化（テスト用）
    app.config['WTF_CSRF_ENABLED'] = False
    # csrf.init_app(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.auth import auth
    
    app.register_blueprint(auth)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        from app.models import FAQ, Conversation, Message, Escalation, User, StaffMember, LoginSession
        db.create_all()
    
    # Context processor for global template variables
    @app.context_processor
    def inject_globals():
        from app.models import Escalation
        from app.auth.utils import get_current_user, generate_csrf_token
        
        current_user = get_current_user()
        return {
            'pending_count': Escalation.get_pending_count(),
            'current_user': current_user,
            'csrf_token': generate_csrf_token
        }
    
    return app