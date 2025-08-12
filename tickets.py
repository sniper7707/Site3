from flask import Blueprint, request, jsonify, session
from models.user import db, Ticket, TicketMessage, User
from datetime import datetime

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')

@tickets_bp.route('/', methods=['GET'])
def get_tickets():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status')
        
        # Build query
        query = Ticket.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter(Ticket.status == status)
        
        # Order by creation date (newest first)
        query = query.order_by(Ticket.created_at.desc())
        
        # Paginate results
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

@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        ticket = Ticket.query.filter_by(id=ticket_id, user_id=user_id).first()
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        return jsonify({'ticket': ticket.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/', methods=['POST'])
def create_ticket():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        user_id = session['user_id']
        
        # Validate required fields
        required_fields = ['subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        subject = data['subject'].strip()
        message = data['message'].strip()
        priority = data.get('priority', 'Normal')
        
        # Validate subject length
        if len(subject) < 5 or len(subject) > 200:
            return jsonify({'error': 'Subject must be between 5 and 200 characters'}), 400
        
        # Validate message length
        if len(message) < 10:
            return jsonify({'error': 'Message must be at least 10 characters'}), 400
        
        # Validate priority
        valid_priorities = ['Low', 'Normal', 'High']
        if priority not in valid_priorities:
            return jsonify({'error': 'Invalid priority'}), 400
        
        # Create ticket
        ticket = Ticket(
            user_id=user_id,
            subject=subject,
            priority=priority,
            status='Open'
        )
        
        db.session.add(ticket)
        db.session.flush()  # Get ticket ID
        
        # Create initial message
        ticket_message = TicketMessage(
            ticket_id=ticket.id,
            user_id=user_id,
            message=message,
            is_admin_reply=False
        )
        
        db.session.add(ticket_message)
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket created successfully',
            'ticket': ticket.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/messages', methods=['GET'])
def get_ticket_messages(ticket_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        # Verify ticket ownership
        ticket = Ticket.query.filter_by(id=ticket_id, user_id=user_id).first()
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Get messages
        messages = TicketMessage.query.filter_by(ticket_id=ticket_id).order_by(
            TicketMessage.created_at.asc()
        ).all()
        
        return jsonify({
            'messages': [message.to_dict() for message in messages]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/messages', methods=['POST'])
def add_ticket_message(ticket_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        user_id = session['user_id']
        
        # Validate required fields
        if not data.get('message'):
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message'].strip()
        
        # Validate message length
        if len(message) < 1:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Verify ticket ownership
        ticket = Ticket.query.filter_by(id=ticket_id, user_id=user_id).first()
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check if ticket is closed
        if ticket.status == 'Closed':
            return jsonify({'error': 'Cannot add message to closed ticket'}), 400
        
        # Create message
        ticket_message = TicketMessage(
            ticket_id=ticket_id,
            user_id=user_id,
            message=message,
            is_admin_reply=False
        )
        
        # Update ticket status
        ticket.status = 'Awaiting Reply'
        ticket.updated_at = datetime.utcnow()
        
        db.session.add(ticket_message)
        db.session.commit()
        
        return jsonify({
            'message': 'Message added successfully',
            'ticket_message': ticket_message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/stats', methods=['GET'])
def get_ticket_stats():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        # Get ticket statistics
        total_tickets = Ticket.query.filter_by(user_id=user_id).count()
        open_tickets = Ticket.query.filter_by(user_id=user_id, status='Open').count()
        answered_tickets = Ticket.query.filter_by(user_id=user_id, status='Answered').count()
        awaiting_tickets = Ticket.query.filter_by(user_id=user_id, status='Awaiting Reply').count()
        closed_tickets = Ticket.query.filter_by(user_id=user_id, status='Closed').count()
        
        return jsonify({
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'answered_tickets': answered_tickets,
            'awaiting_tickets': awaiting_tickets,
            'closed_tickets': closed_tickets
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/close', methods=['POST'])
def close_ticket(ticket_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        # Verify ticket ownership
        ticket = Ticket.query.filter_by(id=ticket_id, user_id=user_id).first()
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Check if ticket is already closed
        if ticket.status == 'Closed':
            return jsonify({'error': 'Ticket is already closed'}), 400
        
        # Close ticket
        ticket.status = 'Closed'
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket closed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

