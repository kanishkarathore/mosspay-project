import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# --- App Setup ---
app = Flask(__name__)
load_dotenv() 

# --- Database Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'mosspay.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a-very-secret-key-you-should-change' 

# --- Database Setup ---
db = SQLAlchemy(app)

# --- Login Manager Setup (FOR CUSTOMERS) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'consumer_login'
login_manager.login_message = 'Please log in to access this page.'

# --- MOCK CARBON DATABASE (50 Items) ---
MOCK_CARBON_DB = {
    # ... (all 50 items) ...
    "Local Apples": 0.2, "Imported Apples": 0.8, "Local Potatoes": 0.1, "Local Tomatoes": 0.3, "Imported Tomatoes": 1.1, "Local Bananas": 0.4, "Imported Bananas": 0.9, "Local Onions": 0.2, "Local Carrots": 0.2, "Organic Spinach": 0.4, "Field-grown Lettuce": 0.3, "Greenhouse Lettuce": 1.2, "Lentils (1kg)": 0.9, "Chickpeas (1kg)": 1.1, "White Rice (1kg)": 2.5, "Brown Rice (1kg)": 2.0, "Oats (1kg)": 0.8, "Whole Wheat Flour (1kg)": 0.6, "White Flour (1kg)": 0.8, "Pasta (500g)": 0.7, "Canned Tomatoes": 0.5, "Canned Beans": 0.4, "Olive Oil (1L)": 3.0, "Sugar (1kg)": 1.2, "Coffee (ground, 500g)": 3.5, "Black Tea (100 bags)": 0.8, "Almond Milk (1L)": 0.7, "Soy Milk (1L)": 0.5, "Oat Milk (1L)": 0.4, "Local Cow's Milk (1L)": 1.5, "Local Cheese (500g)": 4.5, "Local Eggs (12)": 1.2, "Local Chicken (1kg)": 4.5, "Tofu (1kg)": 2.0, "Bamboo Toothbrush": 0.3, "Plastic Toothbrush": 1.5, "Bar Soap (100g)": 0.2, "Liquid Soap (250ml)": 0.8, "Recycled Toilet Paper (4 pack)": 1.0, "Regular Toilet Paper (4 pack)": 2.0, "Eco-friendly Detergent (1L)": 1.5, "Regular Detergent (1L)": 3.0, "Reusable Cleaning Cloth": 0.1, "Jute Bag": 1.5, "Organic Cotton Tote Bag": 1.2, "Reusable Coffee Cup": 1.2, "Reusable Water Bottle": 1.0, "Glass Food Container": 0.8, "Beeswax Wraps (set)": 0.4
}

# --- DATABASE MODELS (TABLES) ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False) # Phone must be unique
    dob = db.Column(db.Date, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    mosscoin_balance = db.Column(db.Integer, default=150)
    total_co2_saved = db.Column(db.Float, default=12.3)
    green_purchases = db.Column(db.Integer, default=5)
    eco_streak = db.Column(db.Integer, default=8)
    rank = db.Column(db.Integer, default=240)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(150), nullable=False)
    contact_name = db.Column(db.String(150), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    udyam_id = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(300), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False) 
    stock = db.Column(db.Integer, nullable=False, default=0)
    carbon_saved_kg = db.Column(db.Float, default=0.0)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    def __repr__(self): return f'<Item {self.name}>'

# --- UPDATED: Bill Model ---
class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    total_carbon_saved = db.Column(db.Float, nullable=False)
    mosscoins_to_award = db.Column(db.Integer, default=0) # <-- NEW COLUMN
    status = db.Column(db.String(20), default='pending') # pending, logged
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_sale = db.Column(db.Float, nullable=False) 
    carbon_at_sale = db.Column(db.Float, nullable=False)

# --- Required function for Flask-Login (FOR CUSTOMERS) ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- FLASK ROUTES ---
@app.route('/')
def welcome_page():
    return render_template('index.html')

# --- Customer Routes ---
@app.route('/consumer/login', methods=['GET', 'POST'])
def consumer_login():
    # ... (code unchanged) ...
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('consumer_dashboard'))
        else:
            flash('Invalid email or password. Please try again.')
            return redirect(url_for('consumer_login'))
    return render_template('consumer_login.html')

@app.route('/consumer/register', methods=['GET', 'POST'])
def consumer_register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        dob_string = request.form.get('dob')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        if password != confirm_password:
            flash("Passwords do not match. Please try again.")
            return redirect(url_for('consumer_register'))
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email already exists.")
            return redirect(url_for('consumer_register'))
        existing_phone = User.query.filter_by(phone=phone).first()
        if existing_phone:
            flash("An account with this phone number already exists.")
            return redirect(url_for('consumer_register'))
        try:
            new_user = User(
                fullname=fullname,
                email=email,
                phone=phone,
                dob=datetime.strptime(dob_string, '%Y-%m-%d').date()
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("User registered successfully!")
            return redirect(url_for('consumer_login'))
        except Exception as e:
            flash(f"An error occurred: {e}")
            db.session.rollback()
            return redirect(url_for('consumer_register'))
    return render_template('consumer_register.html')


@app.route('/consumer/dashboard')
@login_required 
def consumer_dashboard():
    return render_template('consumer_dashboard.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('consumer_login'))

# --- NEW: LOG PURCHASE PAGE ---
@app.route('/consumer/log_purchase')
@login_required
def log_purchase():
    # Find all bills for this user and get the vendor's name
    bills = db.session.query(
        Bill, Vendor.business_name
    ).join(
        Vendor, Bill.vendor_id == Vendor.id
    ).filter(
        Bill.customer_id == current_user.id
    ).order_by(
        Bill.created_at.desc() # Show newest bills first
    ).all()
    
    return render_template('log_purchase.html', bills=bills)

# --- NEW: LOG PURCHASE API ---
@app.route('/api/consumer/log-purchase', methods=['POST'])
@login_required
def api_log_purchase():
    data = request.json
    bill_id = data.get('bill_id')

    if not bill_id:
        return jsonify({'error': 'Missing bill ID.'}), 400

    # 1. Find the bill
    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify({'error': 'Bill not found.'}), 404
        
    # 2. Security Check: Is this bill for the logged-in user?
    if bill.customer_id != current_user.id:
        return jsonify({'error': 'Not authorized.'}), 403
        
    # 3. Status Check: Has it already been logged?
    if bill.status == 'logged':
        return jsonify({'error': 'This bill has already been logged.'}), 400
        
    try:
        # 4. Award points to the user
        current_user.mosscoin_balance += bill.mosscoins_to_award
        current_user.total_co2_saved += bill.total_carbon_saved
        current_user.green_purchases += 1 # Increment green purchase count
        
        # 5. Update the bill status
        bill.status = 'logged'
        
        # 6. Commit all changes to the database
        db.session.commit()
        
        return jsonify({
            'message': 'Purchase logged!',
            'new_balance': current_user.mosscoin_balance,
            'new_co2_saved': current_user.total_co2_saved
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- Vendor Routes ---
@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login():
    # ... (code unchanged) ...
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        vendor = Vendor.query.filter_by(email=email).first()
        if vendor and vendor.check_password(password):
            session['vendor_id'] = vendor.id
            return redirect(url_for('vendor_dashboard'))
        else:
            flash('Invalid email or password. Please try again.')
            return redirect(url_for('vendor_login'))
    return render_template('vendor_login.html')

@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    # ... (code unchanged) ...
    if request.method == 'POST':
        business_name = request.form.get('business-name')
        contact_name = request.form.get('contact-name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        udyam_id = request.form.get('udyam-id')
        address = request.form.get('address')
        if password != confirm_password:
            flash("Passwords do not match. Please try again.")
            return redirect(url_for('vendor_register'))
        existing_vendor = Vendor.query.filter_by(email=email).first()
        if existing_vendor:
            flash("An account with this email already exists.")
            return redirect(url_for('vendor_register'))
        try:
            new_vendor = Vendor(
                business_name=business_name,
                contact_name=contact_name,
                email=email,
                mobile=mobile,
                udyam_id=udyam_id,
                address=address
            )
            new_vendor.set_password(password)
            db.session.add(new_vendor)
            db.session.commit()
            flash("Vendor registered successfully! Please log in.")
            return redirect(url_for('vendor_login'))
        except Exception as e:
            flash(f"An error occurred: {e}")
            db.session.rollback()
            return redirect(url_for('vendor_register'))
    return render_template('vendor_register.html')

@app.route('/vendor/dashboard')
def vendor_dashboard():
    # ... (code unchanged) ...
    if 'vendor_id' not in session:
        flash('You must be logged in to see this page.')
        return redirect(url_for('vendor_login'))
    vendor = Vendor.query.get(session['vendor_id'])
    if not vendor:
        session.pop('vendor_id', None)
        flash('Could not find vendor. Please log in again.')
        return redirect(url_for('vendor_login'))
    return render_template('vendor_dashboard.html', vendor=vendor)

@app.route('/vendor/logout')
def vendor_logout():
    # ... (code unchanged) ...
    session.pop('vendor_id', None)
    flash("You have been logged out.")
    return redirect(url_for('vendor_login'))

@app.route('/vendor/manage_items')
def manage_items():
    # ... (code unchanged) ...
    if 'vendor_id' not in session:
        flash('You must be logged in to see this page.')
        return redirect(url_for('vendor_login'))
    vendor_items = Item.query.filter_by(vendor_id=session['vendor_id']).all()
    return render_template('manage_items.html', items=vendor_items)

@app.route('/api/vendor/add-item', methods=['POST'])
def add_item():
    # ... (code unchanged) ...
    if 'vendor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    data = request.json
    item_name_from_form = data['name']
    carbon_value = 0.0
    for mock_name, mock_value in MOCK_CARBON_DB.items():
        if mock_name.lower() == item_name_from_form.lower():
            carbon_value = mock_value
            break
    try:
        new_item = Item(
            name=item_name_from_form,
            price=float(data['price']),
            unit=data['unit'],
            stock=int(data['stock']),
            carbon_saved_kg=carbon_value,
            vendor_id=session['vendor_id']
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({
            'id': new_item.id,
            'name': new_item.name,
            'price': new_item.price,
            'unit': new_item.unit,
            'stock': new_item.stock,
            'carbon_saved_kg': new_item.carbon_saved_kg
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/vendor/generate_bill')
def generate_bill():
    # ... (code unchanged) ...
    if 'vendor_id' not in session:
        flash('You must be logged in to see this page.')
        return redirect(url_for('vendor_login'))
    vendor_items = Item.query.filter(
        Item.vendor_id == session['vendor_id'],
        Item.stock > 0
    ).all()
    return render_template('generate_bill.html', items=vendor_items)

# --- UPDATED: SEND BILL API ---
@app.route('/api/vendor/send-bill-to-phone', methods=['POST'])
def send_bill_to_phone():
    if 'vendor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    phone_number = data.get('phone')
    cart = data.get('cart') 

    if not phone_number or not cart:
        return jsonify({'error': 'Missing phone number or items.'}), 400

    customer = User.query.filter_by(phone=phone_number).first()
    if not customer:
        return jsonify({'error': f'No MossPay user found with phone number {phone_number}.'}), 404

    total_amount = 0
    total_carbon = 0
    
    with db.session.no_autoflush:
        for cart_item in cart:
            item_id = cart_item['id']
            quantity = cart_item['quantity']
            item_in_db = Item.query.get(item_id)
            if not item_in_db:
                return jsonify({'error': f'Item ID {item_id} not found.'}), 400
            if item_in_db.stock < quantity:
                return jsonify({'error': f'Not enough stock for {item_in_db.name}. Only {item_in_db.stock} left.'}), 400
            total_amount += item_in_db.price * quantity
            total_carbon += item_in_db.carbon_saved_kg * quantity

    # --- THIS IS THE NEW LOGIC ---
    # We will use a simple rule: 10 MossCoins per kg of CO2 saved
    mosscoins = int(total_carbon * 10)
    # --- END NEW LOGIC ---

    try:
        new_bill = Bill(
            vendor_id=session['vendor_id'],
            customer_id=customer.id,
            total_amount=total_amount,
            total_carbon_saved=total_carbon,
            mosscoins_to_award=mosscoins, # <-- SAVING THE REWARD
            status='pending'
        )
        db.session.add(new_bill)
        db.session.commit() # Commit to get the new_bill.id

        for cart_item in cart:
            item_in_db = Item.query.get(cart_item['id'])
            bill_item_entry = BillItem(
                bill_id=new_bill.id,
                item_id=item_in_db.id,
                quantity=cart_item['quantity'],
                price_at_sale=item_in_db.price,
                carbon_at_sale=item_in_db.carbon_saved_kg
            )
            db.session.add(bill_item_entry)
            item_in_db.stock -= cart_item['quantity']
        
        db.session.commit() 
        
        return jsonify({
            'message': f'Bill sent to {customer.fullname}!',
            'bill_id': new_bill.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- Main ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)