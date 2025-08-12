from flask import Blueprint, request, jsonify, session
from models.user import db, Payment, User
from datetime import datetime
import re

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

def validate_phone_number(phone):
    """Validate Egyptian phone number"""
    pattern = r'^(010|011|012|015)\d{8}$'
    return re.match(pattern, phone) is not None

@payments_bp.route('/', methods=['GET'])
def get_payments():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status')
        
        # Build query
        query = Payment.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter(Payment.status == status)
        
        # Order by creation date (newest first)
        query = query.order_by(Payment.created_at.desc())
        
        # Paginate results
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

@payments_bp.route('/', methods=['POST'])
def create_payment():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        user_id = session['user_id']
        
        # Validate required fields
        required_fields = ['amount', 'payment_method', 'transaction_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        amount = float(data['amount'])
        payment_method = data['payment_method']
        transaction_id = data['transaction_id'].strip()
        phone_number = data.get('phone_number', '').strip()
        notes = data.get('notes', '').strip()
        
        # Validate amount
        if amount < 10:
            return jsonify({'error': 'Minimum deposit amount is 10 EGP'}), 400
        
        if amount > 10000:
            return jsonify({'error': 'Maximum deposit amount is 10,000 EGP'}), 400
        
        # Validate payment method
        valid_methods = ['Vodafone Cash', 'Orange Money', 'Etisalat Cash', 'Bank Transfer', 'InstaPay']
        if payment_method not in valid_methods:
            return jsonify({'error': 'Invalid payment method'}), 400
        
        # Validate phone number for mobile wallet payments
        if payment_method in ['Vodafone Cash', 'Orange Money', 'Etisalat Cash']:
            if not phone_number:
                return jsonify({'error': 'Phone number is required for mobile wallet payments'}), 400
            
            if not validate_phone_number(phone_number):
                return jsonify({'error': 'Invalid Egyptian phone number format'}), 400
        
        # Check for duplicate transaction ID
        existing_payment = Payment.query.filter_by(transaction_id=transaction_id).first()
        if existing_payment:
            return jsonify({'error': 'Transaction ID already exists'}), 400
        
        # Create payment request
        payment = Payment(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status='Pending',
            notes=notes
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment request submitted successfully',
            'payment': payment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/methods', methods=['GET'])
def get_payment_methods():
    try:
        methods = [
            {
                'id': 'vodafone_cash',
                'name': 'Vodafone Cash',
                'icon': 'smartphone',
                'instructions': 'قم بالتحويل إلى رقم: 01012345678 ثم أرسل رقم العملية',
                'requires_phone': True
            },
            {
                'id': 'orange_money',
                'name': 'Orange Money',
                'icon': 'smartphone',
                'instructions': 'قم بالتحويل إلى رقم: 01112345678 ثم أرسل رقم العملية',
                'requires_phone': True
            },
            {
                'id': 'etisalat_cash',
                'name': 'Etisalat Cash',
                'icon': 'smartphone',
                'instructions': 'قم بالتحويل إلى رقم: 01512345678 ثم أرسل رقم العملية',
                'requires_phone': True
            },
            {
                'id': 'bank_transfer',
                'name': 'Bank Transfer',
                'icon': 'building-bank',
                'instructions': 'قم بالتحويل إلى حساب: 1234567890 - البنك الأهلي المصري',
                'requires_phone': False
            },
            {
                'id': 'instapay',
                'name': 'InstaPay',
                'icon': 'credit-card',
                'instructions': 'قم بالتحويل عبر InstaPay إلى: sniper.server@instapay.com',
                'requires_phone': False
            }
        ]
        
        return jsonify({'methods': methods}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/stats', methods=['GET'])
def get_payment_stats():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        # Get payment statistics
        total_deposits = db.session.query(db.func.sum(Payment.amount)).filter_by(
            user_id=user_id, status='Approved'
        ).scalar() or 0
        
        pending_deposits = db.session.query(db.func.sum(Payment.amount)).filter_by(
            user_id=user_id, status='Pending'
        ).scalar() or 0
        
        total_payments = Payment.query.filter_by(user_id=user_id).count()
        approved_payments = Payment.query.filter_by(user_id=user_id, status='Approved').count()
        
        # Get current balance
        user = User.query.get(user_id)
        current_balance = float(user.balance) if user else 0
        
        return jsonify({
            'total_deposits': float(total_deposits),
            'pending_deposits': float(pending_deposits),
            'current_balance': current_balance,
            'total_payments': total_payments,
            'approved_payments': approved_payments
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        payment = Payment.query.filter_by(id=payment_id, user_id=user_id).first()
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        return jsonify({'payment': payment.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

