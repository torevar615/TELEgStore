import os
import logging
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app import app
from models import db, Category, File, Subscriber, PendingFile, BroadcastMessage
from sqlalchemy import func
import uuid

# Configure logging
logger = logging.getLogger(__name__)

# Admin authentication
def is_admin():
    """Check if current session is authenticated as admin"""
    admin_id = os.getenv("ADMIN_ID", "")
    return session.get('admin_authenticated') == admin_id

def require_admin(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    """Admin panel dashboard"""
    if not is_admin():
        return redirect(url_for('login'))
    
    categories = Category.query.all()
    files = File.query.all()
    subscribers = Subscriber.query.filter_by(is_active=True).all()
    pending_files = PendingFile.query.all()
    
    stats = {
        'total_categories': len(categories),
        'total_files': len(files),
        'total_subscribers': len(subscribers),
        'pending_files': len(pending_files)
    }
    
    # Bot configuration status
    bot_config = {
        'telegram_bot_token': bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        'admin_id': bool(os.getenv("ADMIN_ID")),
        'storage_channel_id': bool(os.getenv("STORAGE_CHANNEL_ID")),
        'session_secret': bool(os.getenv("SESSION_SECRET"))
    }
    
    return render_template('index.html', stats=stats, pending_files=[pf.to_dict() for pf in pending_files], bot_config=bot_config)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        expected_admin_id = os.getenv("ADMIN_ID", "")
        
        if admin_id == expected_admin_id and expected_admin_id:
            session['admin_authenticated'] = admin_id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid admin ID!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_authenticated', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/categories')
@require_admin
def categories():
    """Categories management page"""
    categories_list = Category.query.all()
    
    # Build category tree
    category_tree = []
    categories_dict = [cat.to_dict() for cat in categories_list]
    
    for category_dict in categories_dict:
        if category_dict.get('parent_id') is None:
            category_dict['subcategories'] = [
                cat for cat in categories_dict 
                if cat.get('parent_id') == category_dict['id']
            ]
            category_tree.append(category_dict)
    
    return render_template('categories.html', categories=category_tree, all_categories=categories_dict)

@app.route('/categories/add', methods=['POST'])
@require_admin
def add_category():
    """Add a new category"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    parent_id = request.form.get('parent_id')
    
    if not name:
        flash('Category name is required!', 'error')
        return redirect(url_for('categories'))
    
    if parent_id == '':
        parent_id = None
    
    category = Category(name=name, description=description, parent_id=parent_id)
    db.session.add(category)
    db.session.commit()
    
    flash(f'Category "{name}" added successfully!', 'success')
    return redirect(url_for('categories'))

@app.route('/categories/<category_id>/edit', methods=['POST'])
@require_admin
def edit_category(category_id):
    """Edit a category"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Category name is required!', 'error')
        return redirect(url_for('categories'))
    
    category = Category.query.get(category_id)
    if category:
        category.name = name
        category.description = description
        db.session.commit()
        flash(f'Category "{name}" updated successfully!', 'success')
    else:
        flash('Category not found!', 'error')
    
    return redirect(url_for('categories'))

@app.route('/categories/<category_id>/delete', methods=['POST'])
@require_admin
def delete_category(category_id):
    """Delete a category"""
    category = Category.query.get(category_id)
    if category:
        # Delete associated files first
        File.query.filter_by(category_id=category_id).delete()
        # Delete subcategories recursively
        def delete_subcategories(parent_id):
            subcats = Category.query.filter_by(parent_id=parent_id).all()
            for subcat in subcats:
                delete_subcategories(subcat.id)
                File.query.filter_by(category_id=subcat.id).delete()
                db.session.delete(subcat)
        
        delete_subcategories(category_id)
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category.name}" deleted successfully!', 'success')
    else:
        flash('Category not found!', 'error')
    
    return redirect(url_for('categories'))

@app.route('/files')
@require_admin
def files():
    """Files management page"""
    files_list = File.query.all()
    categories_list = Category.query.all()
    pending_files = PendingFile.query.all()
    
    # Create category lookup
    category_map = {cat.id: cat.name for cat in categories_list}
    
    # Add category names to files
    files_dict = []
    for file_item in files_list:
        file_dict = file_item.to_dict()
        file_dict['category_name'] = category_map.get(file_item.category_id, 'Unknown')
        files_dict.append(file_dict)
    
    return render_template('files.html', 
                         files=files_dict, 
                         categories=[cat.to_dict() for cat in categories_list],
                         pending_files=[pf.to_dict() for pf in pending_files])

@app.route('/files/add', methods=['POST'])
@require_admin
def add_file():
    """Add a new file"""
    name = request.form.get('name', '').strip()
    category_id = request.form.get('category_id')
    description = request.form.get('description', '').strip()
    telegram_file_id = request.form.get('telegram_file_id', '').strip()
    
    if not name or not category_id:
        flash('File name and category are required!', 'error')
        return redirect(url_for('files'))
    
    file_obj = File(name=name, category_id=category_id, telegram_file_id=telegram_file_id, description=description)
    db.session.add(file_obj)
    db.session.commit()
    
    flash(f'File "{name}" added successfully!', 'success')
    return redirect(url_for('files'))

@app.route('/files/add_pending/<pending_id>', methods=['POST'])
@require_admin
def add_pending_file(pending_id):
    """Add a pending file to a category"""
    category_id = request.form.get('category_id')
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not category_id or not name:
        flash('Category and file name are required!', 'error')
        return redirect(url_for('files'))
    
    # Get pending file
    pending_file = PendingFile.query.get(pending_id)
    
    if not pending_file:
        flash('Pending file not found!', 'error')
        return redirect(url_for('files'))
    
    # Add file to storage
    file_obj = File(
        name=name,
        category_id=category_id,
        telegram_file_id=pending_file.telegram_file_id,
        description=description,
        size=pending_file.size,
        mime_type=pending_file.mime_type
    )
    db.session.add(file_obj)
    
    # Remove from pending
    db.session.delete(pending_file)
    db.session.commit()
    
    flash(f'File "{name}" added successfully!', 'success')
    return redirect(url_for('files'))

@app.route('/files/<file_id>/edit', methods=['POST'])
@require_admin
def edit_file(file_id):
    """Edit a file"""
    name = request.form.get('name', '').strip()
    category_id = request.form.get('category_id')
    description = request.form.get('description', '').strip()
    telegram_file_id = request.form.get('telegram_file_id', '').strip()
    
    if not name or not category_id:
        flash('File name and category are required!', 'error')
        return redirect(url_for('files'))
    
    file_obj = File.query.get(file_id)
    if file_obj:
        file_obj.name = name
        file_obj.category_id = category_id
        file_obj.description = description
        file_obj.telegram_file_id = telegram_file_id
        db.session.commit()
        flash(f'File "{name}" updated successfully!', 'success')
    else:
        flash('File not found!', 'error')
    
    return redirect(url_for('files'))

@app.route('/files/<file_id>/delete', methods=['POST'])
@require_admin
def delete_file(file_id):
    """Delete a file"""
    file_item = File.query.get(file_id)
    if file_item:
        db.session.delete(file_item)
        db.session.commit()
        flash(f'File "{file_item.name}" deleted successfully!', 'success')
    else:
        flash('File not found!', 'error')
    
    return redirect(url_for('files'))

@app.route('/broadcast')
@require_admin
def broadcast():
    """Broadcast management page"""
    subscribers = Subscriber.query.filter_by(is_active=True).all()
    return render_template('broadcast.html', subscriber_count=len(subscribers))

@app.route('/broadcast/send', methods=['POST'])
@require_admin
def send_broadcast():
    """Send broadcast message"""
    message = request.form.get('message', '').strip()
    
    if not message:
        flash('Message is required!', 'error')
        return redirect(url_for('broadcast'))
    
    try:
        import asyncio
        import os
        from telegram import Bot
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            flash('Bot token not configured!', 'error')
            return redirect(url_for('broadcast'))
        
        # Get active subscribers
        subscribers = Subscriber.query.filter_by(is_active=True).all()
        
        if not subscribers:
            flash('No active subscribers found!', 'warning')
            return redirect(url_for('broadcast'))
        
        # Create broadcast record
        broadcast_msg = BroadcastMessage(
            message=message,
            sent_to_count=0,
            failed_count=0
        )
        db.session.add(broadcast_msg)
        db.session.commit()
        
        # Send broadcast asynchronously
        async def send_broadcast():
            bot = Bot(token=bot_token)
            sent_count = 0
            failed_count = 0
            
            for subscriber in subscribers:
                try:
                    await bot.send_message(
                        chat_id=subscriber.user_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send to {subscriber.user_id}: {e}")
                    failed_count += 1
            
            # Update broadcast record
            broadcast_msg.sent_to_count = sent_count
            broadcast_msg.failed_count = failed_count
            db.session.commit()
            
            return sent_count, failed_count
        
        # Run the broadcast
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sent_count, failed_count = loop.run_until_complete(send_broadcast())
        loop.close()
        
        flash(f'Broadcast sent to {sent_count} subscribers! {failed_count} failed.', 'success')
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        flash('Error sending broadcast!', 'error')
    
    return redirect(url_for('broadcast'))

@app.route('/api/subscribers')
@require_admin
def api_subscribers():
    """API endpoint for subscriber data"""
    subscribers = Subscriber.query.filter_by(is_active=True).all()
    return jsonify({
        'count': len(subscribers),
        'subscribers': [sub.to_dict() for sub in subscribers]
    })

# Template context processors
@app.context_processor
def inject_user():
    return dict(is_admin=is_admin())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
