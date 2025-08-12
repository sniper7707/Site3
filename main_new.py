import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, session
from src.models.user import db, User, Service, Order, Payment, Ticket, TicketMessage, Notification, SiteSetting
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.services import services_bp
from src.routes.orders import orders_bp
from src.routes.payments import payments_bp
from src.routes.tickets import tickets_bp
from flask_cors import CORS

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'sniper-server-secret-key-2025-alaa-badeeh'

# تمكين CORS للسماح بالطلبات من الواجهة الأمامية
CORS(app, supports_credentials=True)

# تسجيل جميع الـ blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp)
app.register_blueprint(services_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(tickets_bp)

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def create_sample_services():
    """إنشاء خدمات تجريبية للاختبار"""
    sample_services = [
        # خدمات إنستغرام
        {
            'name': 'متابعين إنستغرام عرب حقيقيين',
            'platform': 'Instagram',
            'service_type': 'followers',
            'price_per_1000': 15.00,
            'min_quantity': 100,
            'max_quantity': 50000,
            'description': 'متابعين عرب حقيقيين ونشطين لحسابك على إنستغرام'
        },
        {
            'name': 'لايكات إنستغرام سريعة',
            'platform': 'Instagram',
            'service_type': 'likes',
            'price_per_1000': 8.50,
            'min_quantity': 50,
            'max_quantity': 10000,
            'description': 'لايكات سريعة وآمنة لمنشوراتك على إنستغرام'
        },
        {
            'name': 'مشاهدات ريلز إنستغرام',
            'platform': 'Instagram',
            'service_type': 'views',
            'price_per_1000': 5.00,
            'min_quantity': 1000,
            'max_quantity': 100000,
            'description': 'مشاهدات عالية الجودة لفيديوهات الريلز'
        },
        # خدمات فيسبوك
        {
            'name': 'لايكات فيسبوك للصفحات',
            'platform': 'Facebook',
            'service_type': 'likes',
            'price_per_1000': 12.00,
            'min_quantity': 100,
            'max_quantity': 25000,
            'description': 'لايكات حقيقية لصفحتك على فيسبوك'
        },
        {
            'name': 'متابعين فيسبوك عرب',
            'platform': 'Facebook',
            'service_type': 'followers',
            'price_per_1000': 18.00,
            'min_quantity': 100,
            'max_quantity': 30000,
            'description': 'متابعين عرب نشطين لصفحتك على فيسبوك'
        },
        # خدمات يوتيوب
        {
            'name': 'مشاهدات يوتيوب عالية الجودة',
            'platform': 'YouTube',
            'service_type': 'views',
            'price_per_1000': 3.50,
            'min_quantity': 1000,
            'max_quantity': 500000,
            'description': 'مشاهدات حقيقية وآمنة لفيديوهاتك على يوتيوب'
        },
        {
            'name': 'مشتركين يوتيوب حقيقيين',
            'platform': 'YouTube',
            'service_type': 'subscribers',
            'price_per_1000': 45.00,
            'min_quantity': 50,
            'max_quantity': 10000,
            'description': 'مشتركين حقيقيين ونشطين لقناتك على يوتيوب'
        },
        # خدمات تويتر
        {
            'name': 'متابعين تويتر عرب',
            'platform': 'Twitter',
            'service_type': 'followers',
            'price_per_1000': 20.00,
            'min_quantity': 100,
            'max_quantity': 20000,
            'description': 'متابعين عرب حقيقيين لحسابك على تويتر'
        },
        {
            'name': 'ريتويت تويتر',
            'platform': 'Twitter',
            'service_type': 'retweets',
            'price_per_1000': 25.00,
            'min_quantity': 50,
            'max_quantity': 5000,
            'description': 'ريتويت حقيقي لتغريداتك على تويتر'
        },
        # خدمات تيك توك
        {
            'name': 'متابعين تيك توك عرب',
            'platform': 'TikTok',
            'service_type': 'followers',
            'price_per_1000': 22.00,
            'min_quantity': 100,
            'max_quantity': 25000,
            'description': 'متابعين عرب حقيقيين لحسابك على تيك توك'
        },
        {
            'name': 'مشاهدات تيك توك',
            'platform': 'TikTok',
            'service_type': 'views',
            'price_per_1000': 2.50,
            'min_quantity': 1000,
            'max_quantity': 1000000,
            'description': 'مشاهدات عالية الجودة لفيديوهاتك على تيك توك'
        },
        {
            'name': 'لايكات تيك توك',
            'platform': 'TikTok',
            'service_type': 'likes',
            'price_per_1000': 15.00,
            'min_quantity': 100,
            'max_quantity': 50000,
            'description': 'لايكات حقيقية لفيديوهاتك على تيك توك'
        }
    ]
    
    for service_data in sample_services:
        service = Service(**service_data)
        db.session.add(service)
    
    db.session.commit()
    print("تم إنشاء الخدمات التجريبية بنجاح!")

with app.app_context():
    db.create_all()
    
    # إنشاء خدمات تجريبية إذا كانت قاعدة البيانات فارغة
    if Service.query.count() == 0:
        create_sample_services()

# نقاط النهاية الأساسية
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Sniper Server API is running',
        'version': '1.0.0',
        'owner': '👑 alaa badeeh 👑'
    })

@app.route('/api')
def api_info():
    return jsonify({
        'message': 'Welcome to Sniper Server API',
        'owner': '👑 alaa badeeh 👑',
        'endpoints': {
            'auth': '/api/auth',
            'services': '/api/services',
            'orders': '/api/orders',
            'payments': '/api/payments',
            'tickets': '/api/tickets',
            'health': '/api/health'
        }
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

