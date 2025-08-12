from flask import Blueprint, request, jsonify, session
from models.user import db, Service
from sqlalchemy import or_

services_bp = Blueprint('services', __name__, url_prefix='/api/services')

@services_bp.route('/', methods=['GET'])
def get_services():
    try:
        # Get query parameters
        platform = request.args.get('platform')
        category = request.args.get('category')
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query
        query = Service.query.filter_by(is_active=True)
        
        if platform:
            query = query.filter(Service.platform == platform)
        
        if category:
            query = query.filter(Service.service_type == category)
        
        if search:
            query = query.filter(
                or_(
                    Service.name.contains(search),
                    Service.description.contains(search)
                )
            )
        
        # Paginate results
        services = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'services': [service.to_dict() for service in services.items],
            'total': services.total,
            'pages': services.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@services_bp.route('/<int:service_id>', methods=['GET'])
def get_service(service_id):
    try:
        service = Service.query.get(service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        if not service.is_active:
            return jsonify({'error': 'Service is not available'}), 400
        
        return jsonify({'service': service.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@services_bp.route('/platforms', methods=['GET'])
def get_platforms():
    try:
        platforms = db.session.query(Service.platform).filter_by(is_active=True).distinct().all()
        platform_list = [platform[0] for platform in platforms]
        
        return jsonify({'platforms': platform_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@services_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        platform = request.args.get('platform')
        
        query = db.session.query(Service.service_type).filter_by(is_active=True)
        
        if platform:
            query = query.filter(Service.platform == platform)
        
        categories = query.distinct().all()
        category_list = [category[0] for category in categories]
        
        return jsonify({'categories': category_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@services_bp.route('/popular', methods=['GET'])
def get_popular_services():
    try:
        # Get most ordered services (you can implement this based on order count)
        # For now, just return first 6 active services
        services = Service.query.filter_by(is_active=True).limit(6).all()
        
        return jsonify({
            'services': [service.to_dict() for service in services]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@services_bp.route('/calculate-price', methods=['POST'])
def calculate_price():
    try:
        data = request.get_json()
        
        service_id = data.get('service_id')
        quantity = data.get('quantity')
        
        if not service_id or not quantity:
            return jsonify({'error': 'Service ID and quantity are required'}), 400
        
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
        
        # Calculate price
        price = (quantity / 1000) * float(service.price_per_1000)
        
        return jsonify({
            'service_id': service_id,
            'quantity': quantity,
            'price_per_1000': float(service.price_per_1000),
            'total_price': round(price, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

