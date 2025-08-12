from flask import Blueprint, request, jsonify, session
from models.user import db, User, Service, Order, Payment, Ticket, TicketMessage
from datetime import datetime, timedelta
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def require_admin():
    """Decorator to require admin authentication"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    return None

# Dashboard Stats
@admin_bp.route('/stats', methods=['GET'])
def get_admin_stats():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        # Basic stats
        total_users = User.query.count()
        total_orders = Order.query.count()
        total_services = Service.query.filter_by(is_active=True).count()
        pending_tickets = Ticket.query.filter_by(status='Open').count()
        
        # Revenue stats
        total_revenue = db.session.query(func.sum(Order.charge)).filter_by(status='Completed').scalar() or 0
        pending_payments = Payment.query.filter_by(status='Pending').count()
        
        # Today's stats
        today = datetime.utcnow().date()
        today_orders = Order.query.filter(func.date(Order.created_at) == today).count()
        today_revenue = db.session.query(func.sum(Order.charge)).filter(
            func.date(Order.created_at) == today,
            Order.status == 'Completed'
        ).scalar() or 0
        
        # Recent activity
        recent_orders = Order.query.order_by(desc(Order.created_at)).limit(5).all()
        recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
        
        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_orders': total_orders,
                'total_services': total_services,
                'pending_tickets': pending_tickets,
                'total_revenue': float(total_revenue),
                'pending_payments': pending_payments,
                'today_orders': today_orders,
                'today_revenue': float(today_revenue)
            },
            'recent_orders': [order.to_dict() for order in recent_orders],
            'recent_users': [user.to_dict() for user in recent_users]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Orders Management
@admin_bp.route('/orders', methods=['GET'])
def get_admin_orders():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status')
        
        query = Order.query
        
        if status:
            query = query.filter(Order.status == status)
        
        query = query.order_by(desc(Order.created_at))
        
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

@admin_bp.route('/orders/<int:order_id>/update', methods=['POST'])
def update_order_status(order_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        valid_statuses = ['Pending', 'In Progress', 'Completed', 'Cancelled', 'Refunded']
        if new_status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        old_status = order.status
        order.status = new_status
        order.notes = notes
        order.updated_at = datetime.utcnow()
        
        # Handle refunds
        if new_status == 'Refunded' and old_status != 'Refunded':
            user = User.query.get(order.user_id)
            user.balance = float(user.balance) + float(order.charge)
        
        # Set completion date
        if new_status == 'Completed':
            order.completed_at = datetime.utcnow()
            order.remains = 0
        
        db.session.commit()
        
        return jsonify({
            'message': 'Order updated successfully',
            'order': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Users Management
@admin_bp.route('/users', methods=['GET'])
def get_admin_users():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search')
        
        query = User.query
        
        if search:
            query = query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search))
            )
        
        query = query.order_by(desc(User.created_at))
        
        users = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/balance', methods=['POST'])
def update_user_balance(user_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        action = data.get('action')  # 'add' or 'set'
        
        if action not in ['add', 'set']:
            return jsonify({'error': 'Invalid action'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if action == 'add':
            user.balance = float(user.balance) + amount
        else:  # set
            user.balance = amount
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Balance updated successfully',
            'new_balance': float(user.balance)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Payments Management
@admin_bp.route('/payments', methods=['GET'])
def get_admin_payments():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status')
        
        query = Payment.query
        
        if status:
            query = query.filter(Payment.status == status)
        
        query = query.order_by(desc(Payment.created_at))
        
        payments = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments.items],
            'total': payments.total,
            'pages': payments.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/payments/<int:payment_id>/approve', methods=['POST'])
def approve_payment(payment_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.get_json()
        admin_notes = data.get('notes', '')
        
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        if payment.status != 'Pending':
            return jsonify({'error': 'Payment is not pending'}), 400
        
        # Update payment
        payment.status = 'Approved'
        payment.notes = admin_notes
        payment.updated_at = datetime.utcnow()
        
        # Add balance to user
        user = User.query.get(payment.user_id)
        user.balance = float(user.balance) + float(payment.amount)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment approved successfully',
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/payments/<int:payment_id>/reject', methods=['POST'])
def reject_payment(payment_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.get_json()
        admin_notes = data.get('notes', '')
        
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        if payment.status != 'Pending':
            return jsonify({'error': 'Payment is not pending'}), 400
        
        # Update payment
        payment.status = 'Rejected'
        payment.notes = admin_notes
        payment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Payment rejected successfully',
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Tickets Management
@admin_bp.route('/tickets', methods=['GET'])
def get_admin_tickets():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status')
        
        query = Ticket.query
        
        if status:
            query = query.filter(Ticket.status == status)
        
        query = query.order_by(desc(Ticket.created_at))
        
        tickets = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'tickets': [ticket.to_dict() for ticket in tickets.items],
            'total': tickets.total,
            'pages': tickets.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/tickets/<int:ticket_id>/reply', methods=['POST'])
def reply_to_ticket(ticket_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Create admin reply
        ticket_message = TicketMessage(
            ticket_id=ticket_id,
            user_id=None,  # Admin message
            message=message,
            is_admin_reply=True
        )
        
        # Update ticket status
        ticket.status = 'Answered'
        ticket.updated_at = datetime.utcnow()
        
        db.session.add(ticket_message)
        db.session.commit()
        
        return jsonify({
            'message': 'Reply sent successfully',
            'ticket_message': ticket_message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/tickets/<int:ticket_id>/close', methods=['POST'])
def close_admin_ticket(ticket_id):
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        ticket.status = 'Closed'
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket closed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

