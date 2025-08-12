from flask import Blueprint, request, jsonify, session
from models.user import db, Order, Service, User
from datetime import datetime
import re

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

def validate_url(url):
    """Validate if URL is a valid social media URL"""
    patterns = [
        r'https?://(www\.)?(instagram\.com|facebook\.com|youtube\.com|twitter\.com|tiktok\.com)',
        r'https?://(www\.)?(instagram\.com|facebook\.com|youtube\.com|twitter\.com|tiktok\.com)/.*',
        r'@[a-zA-Z0-9_.]+',  # Username format
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    return False

@orders_bp.route('/', methods=['GET'])
def get_orders():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status')
        
        # Build query
        query = Order.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        # Order by creation date (newest first)
        query = query.order_by(Order.created_at.desc())
        
        # Paginate results
        orders = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'orders': [order.to_dict() for order in orders.items],
            'total': orders.total,
            'pages': orders.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        return jsonify({'order': order.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/', methods=['POST'])
def create_order():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        user_id = session['user_id']
        
        # Validate required fields
        required_fields = ['service_id', 'quantity', 'link']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        service_id = data['service_id']
        quantity = int(data['quantity'])
        link = data['link'].strip()
        
        # Get service
        service = Service.query.get(service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        if not service.is_active:
            return jsonify({'error': 'Service is not available'}), 400
        
        # Validate quantity
        if quantity < service.min_quantity:
            return jsonify({'error': f'Minimum quantity is {service.min_quantity}'}), 400
        
        if quantity > service.max_quantity:
            return jsonify({'error': f'Maximum quantity is {service.max_quantity}'}), 400
        
        # Validate URL/link
        if not validate_url(link):
            return jsonify({'error': 'Invalid URL or username format'}), 400
        
        # Calculate price
        total_price = (quantity / 1000) * float(service.price_per_1000)
        
        # Get user and check balance
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if float(user.balance) < total_price:
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Create order
        order = Order(
            user_id=user_id,
            service_id=service_id,
            link=link,
            quantity=quantity,
            charge=total_price,
            remains=quantity,
            status='Pending'
        )
        
        # Deduct balance
        user.balance = float(user.balance) - total_price
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'message': 'Order created successfully',
            'order': order.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/stats', methods=['GET'])
def get_order_stats():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        # Get order statistics
        total_orders = Order.query.filter_by(user_id=user_id).count()
        pending_orders = Order.query.filter_by(user_id=user_id, status='Pending').count()
        in_progress_orders = Order.query.filter_by(user_id=user_id, status='In Progress').count()
        completed_orders = Order.query.filter_by(user_id=user_id, status='Completed').count()
        
        # Calculate total spent
        total_spent = db.session.query(db.func.sum(Order.charge)).filter_by(user_id=user_id).scalar() or 0
        
        return jsonify({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'in_progress_orders': in_progress_orders,
            'completed_orders': completed_orders,
            'total_spent': float(total_spent)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Only allow cancellation of pending orders
        if order.status != 'Pending':
            return jsonify({'error': 'Only pending orders can be cancelled'}), 400
        
        # Refund balance
        user = User.query.get(user_id)
        user.balance = float(user.balance) + float(order.charge)
        
        # Update order status
        order.status = 'Cancelled'
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Order cancelled successfully',
            'refunded_amount': float(order.charge)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

