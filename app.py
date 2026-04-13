from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from PIL import Image
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Use /tmp for SQLite on Render (writable location)
db_path = os.path.join('/tmp', 'photos.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure upload folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='client', lazy=True)
    photos = db.relationship('Photo', backref='client', lazy=True)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    thumbnail_path = db.Column(db.String(500))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    session_type = db.Column(db.String(50), nullable=False)
    session_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    special_requests = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_thumbnail(input_path, output_path, size=(300, 300)):
    try:
        with Image.open(input_path) as img:
            img.thumbnail(size)
            img.save(output_path, optimize=True, quality=85)
    except Exception as e:
        print(f"Thumbnail error: {e}")

# Create tables before first request
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    recent_photos = Photo.query.order_by(Photo.uploaded_at.desc()).limit(8).all()
    return render_template('index.html', recent_photos=recent_photos)

@app.route('/gallery')
def gallery():
    category = request.args.get('category', 'all')
    if category and category != 'all':
        photos = Photo.query.filter_by(category=category).order_by(Photo.uploaded_at.desc()).all()
    else:
        photos = Photo.query.order_by(Photo.uploaded_at.desc()).all()
    
    categories = db.session.query(Photo.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('gallery.html', photos=photos, categories=categories, active_category=category)

@app.route('/upload', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('gallery'))
    
    file = request.files['photo']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('gallery'))
    
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Create thumbnail
        thumb_filename = f"thumb_{unique_filename}"
        thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_filename)
        create_thumbnail(file_path, thumb_path)
        
        # Save to database
        photo = Photo(
            filename=unique_filename,
            original_filename=original_filename,
            file_path=f"/static/uploads/{unique_filename}",
            thumbnail_path=f"/static/uploads/{thumb_filename}",
            description=request.form.get('description', ''),
            category=request.form.get('category', 'uncategorized')
        )
        
        db.session.add(photo)
        db.session.commit()
        
        flash('Photo uploaded successfully!', 'success')
    
    return redirect(url_for('gallery'))

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        session_type = request.form.get('session_type')
        session_date = request.form.get('session_date')
        special_requests = request.form.get('special_requests')
        
        # Create or get client
        client = Client.query.filter_by(email=email).first()
        if not client:
            client = Client(name=name, email=email, phone=phone)
            db.session.add(client)
            db.session.commit()
        
        # Create booking
        booking = Booking(
            client_id=client.id,
            session_type=session_type,
            session_date=datetime.strptime(session_date, '%Y-%m-%d'),
            special_requests=special_requests
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash('Booking request submitted successfully! We will contact you soon.', 'success')
        return redirect(url_for('booking'))
    
    return render_template('booking.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        message = ContactMessage(
            name=request.form.get('name'),
            email=request.form.get('email'),
            message=request.form.get('message')
        )
        db.session.add(message)
        db.session.commit()
        
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/dashboard')
def dashboard():
    total_clients = Client.query.count()
    total_bookings = Booking.query.count()
    total_photos = Photo.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    recent_photos = Photo.query.order_by(Photo.uploaded_at.desc()).limit(6).all()
    
    return render_template('dashboard.html', 
                         total_clients=total_clients,
                         total_bookings=total_bookings,
                         total_photos=total_photos,
                         pending_bookings=pending_bookings,
                         recent_bookings=recent_bookings,
                         recent_photos=recent_photos)

@app.route('/api/photos')
def api_photos():
    photos = Photo.query.all()
    return jsonify([{
        'id': p.id,
        'url': p.thumbnail_path,
        'category': p.category,
        'description': p.description
    } for p in photos])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=5000)