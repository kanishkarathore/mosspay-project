import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# --- WEB3 IMPORTS ---
from algosdk.v2client import algod
from algosdk import transaction, mnemonic, account
from algosdk.logic import get_application_address

# --- LOGISTICS IMPORTS ---
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

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

# --- CARBON FOOTPRINT DATABASE ---
CARBON_FOOTPRINT_DB = {
    "Food & Produce": {
        "Apple": {"sustainable_kg": 0.3, "unsustainable_kg": 0.8},
        "Tomatoes": {"sustainable_kg": 0.5, "unsustainable_kg": 2.5},
        "Oat Milk": {"sustainable_kg": 0.9, "unsustainable_kg": 3.2},
        "Milk": {"sustainable_kg": 1.5, "unsustainable_kg": 3.2},
        "Tofu": {"sustainable_kg": 2.0, "unsustainable_kg": 6.9},
        "Lentils": {"sustainable_kg": 0.9, "unsustainable_kg": 50.0},
        "Bread": {"sustainable_kg": 0.6, "unsustainable_kg": 1.0},
        "Eggs": {"sustainable_kg": 2.1, "unsustainable_kg": 3.5},
        "Potatoes": {"sustainable_kg": 0.1, "unsustainable_kg": 0.5},
        "Rice": {"sustainable_kg": 2.0, "unsustainable_kg": 2.5},
        "Coffee": {"sustainable_kg": 3.5, "unsustainable_kg": 7.0},
        "Tea": {"sustainable_kg": 0.8, "unsustainable_kg": 1.6},
    },
    "Bags & Containers": {
        "Jute Bag": {"sustainable_kg": 0.2, "unsustainable_kg": 1.8},
        "Cotton Tote Bag": {"sustainable_kg": 0.5, "unsustainable_kg": 1.8},
        "Beeswax Wraps": {"sustainable_kg": 0.1, "unsustainable_kg": 0.5},
        "Reusable Water Bottle": {"sustainable_kg": 0.8, "unsustainable_kg": 21.0}, 
        "Reusable Coffee Cup": {"sustainable_kg": 0.5, "unsustainable_kg": 15.0},
        "Glass Food Container": {"sustainable_kg": 0.8, "unsustainable_kg": 1.5},
    },
    "Household": {
        "Recycled Toilet Paper": {"sustainable_kg": 1.0, "unsustainable_kg": 2.0},
        "Eco-friendly Detergent": {"sustainable_kg": 1.5, "unsustainable_kg": 3.0},
        "LED Bulb": {"sustainable_kg": 0.2, "unsustainable_kg": 1.0},
        "Compost Bin": {"sustainable_kg": 2.0, "unsustainable_kg": 5.0},
        "Reusable Cleaning Cloth": {"sustainable_kg": 0.1, "unsustainable_kg": 0.5},
    },
    "Personal Care": {
        "Bamboo Toothbrush": {"sustainable_kg": 0.1, "unsustainable_kg": 0.8},
        "Bar Soap": {"sustainable_kg": 0.2, "unsustainable_kg": 0.6},
        "Shampoo Bar": {"sustainable_kg": 0.1, "unsustainable_kg": 0.7},
        "Reusable Makeup Pad": {"sustainable_kg": 0.05, "unsustainable_kg": 0.3},
    },
    "Artifacts & Decor": {
        "Terracotta Pot": {"sustainable_kg": 1.0, "unsustainable_kg": 3.5},
        "Handwoven Rug": {"sustainable_kg": 2.0, "unsustainable_kg": 10.0},
        "Recycled Glass Vase": {"sustainable_kg": 0.8, "unsustainable_kg": 2.0},
        "Wooden Bowl": {"sustainable_kg": 0.5, "unsustainable_kg": 1.5},
    }
}

MOCK_REWARDS_DB = {
    "gov_1": {"type": "Government Scheme", "title": "Plant a Tree in Your Name", "description": "We'll partner with a local NGO to plant a tree.", "cost": 500},
    "gov_2": {"type": "Government Scheme", "title": "Solar Panel Subsidy Voucher", "description": "Claim a voucher for an extra 5% off a solar panel installation.", "cost": 5000}
}

# --- DATABASE MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False) 
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
    description = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.String(300), nullable=True)
    shop_category = db.Column(db.String(100), nullable=True)
    website_url = db.Column(db.String(300), nullable=True)
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
    bill_items = db.relationship('BillItem', back_populates='item', lazy=True)
    def __repr__(self): return f'<Item {self.name}>'

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    total_carbon_saved = db.Column(db.Float, nullable=False)
    mosscoins_to_award = db.Column(db.Integer, default=0) 
    status = db.Column(db.String(20), default='pending') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('BillItem', back_populates='bill', lazy='joined')

class BillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_sale = db.Column(db.Float, nullable=False) 
    carbon_at_sale = db.Column(db.Float, nullable=False)
    bill = db.relationship('Bill', back_populates='items')
    item = db.relationship('Item', back_populates='bill_items', lazy='joined')

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    mosscoin_cost = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='active') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class B2BOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_paid = db.Column(db.Float, nullable=False)
    carbon_saved = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    buyer = db.relationship('Vendor', foreign_keys=[buyer_id])
    seller = db.relationship('Vendor', foreign_keys=[seller_id])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- LOGISTICS CALCULATOR ---
def calculate_shop_distance(buyer_address, seller_address):
    """Converts text addresses to Lat/Lng and calculates distance in KM."""
    geolocator = Nominatim(user_agent="mosspay_carbon_engine")
    try:
        loc1 = geolocator.geocode(f"{buyer_address}, India")
        loc2 = geolocator.geocode(f"{seller_address}, India")
        if loc1 and loc2:
            coords_1 = (loc1.latitude, loc1.longitude)
            coords_2 = (loc2.latitude, loc2.longitude)
            return round(geodesic(coords_1, coords_2).kilometers, 2)
        return 15.0 # Fallback 
    except Exception as e:
        print(f"Map API warning: {e}")
        return 15.0 # Fallback

# --- FLASK ROUTES ---
@app.route('/')
def welcome_page():
    return render_template('index.html')

# --- Customer Routes ---
@app.route('/consumer/login', methods=['GET', 'POST'])
def consumer_login():
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
        try:
            new_user = User(
                fullname=fullname, email=email, phone=phone,
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
    GOAL_CO2 = 100.0 
    current_tree_co2 = current_user.total_co2_saved % GOAL_CO2
    growth_percent = (current_tree_co2 / GOAL_CO2) * 100
    trees_planted = int(current_user.total_co2_saved // GOAL_CO2)
    return render_template('consumer_dashboard.html', user=current_user, growth_percent=growth_percent, trees_planted=trees_planted)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('consumer_login'))

@app.route('/consumer/log_purchase')
@login_required
def log_purchase():
    bills = db.session.query(Bill, Vendor.business_name).join(Vendor, Bill.vendor_id == Vendor.id).filter(Bill.customer_id == current_user.id).order_by(Bill.created_at.desc()).all()
    return render_template('log_purchase.html', bills=bills)

@app.route('/api/consumer/log-purchase', methods=['POST'])
@login_required
def api_log_purchase():
    data = request.json
    bill = Bill.query.get(data.get('bill_id'))
    if not bill: return jsonify({'error': 'Bill not found.'}), 404
    if bill.customer_id != current_user.id: return jsonify({'error': 'Not authorized.'}), 403
    if bill.status == 'logged': return jsonify({'error': 'This bill has already been logged.'}), 400
    try:
        current_user.mosscoin_balance += bill.mosscoins_to_award
        current_user.total_co2_saved += bill.total_carbon_saved
        current_user.green_purchases += 1
        bill.status = 'logged'
        db.session.commit()
        return jsonify({'message': 'Purchase logged!', 'new_balance': current_user.mosscoin_balance, 'new_co2_saved': current_user.total_co2_saved}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/consumer/discover_vendors')
@login_required
def discover_vendors():
    search_term = request.args.get('q')
    if search_term:
        vendor_ids = [v_id[0] for v_id in db.session.query(Item.vendor_id).filter(Item.name.ilike(f'%{search_term}%')).distinct().all()]
        vendors = Vendor.query.filter(Vendor.id.in_(vendor_id_list)).all()
    else:
        vendors = Vendor.query.all()
    return render_template('discover_vendors.html', vendors=vendors, search_term=search_term)

@app.route('/vendor_profile/<int:vendor_id>')
@login_required
def vendor_profile(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    items = Item.query.filter_by(vendor_id=vendor.id).all()
    return render_template('vendor_profile.html', vendor=vendor, items=items)

@app.route('/consumer/leaderboard')
@login_required
def leaderboard():
    return render_template('leaderboard.html', users=User.query.order_by(User.total_co2_saved.desc()).all())

@app.route('/consumer/my_sprout')
@login_required
def my_sprout():
    GOAL_CO2 = 100.0 
    return render_template('my_sprout.html', user=current_user, growth_percent=((current_user.total_co2_saved % GOAL_CO2) / GOAL_CO2) * 100, trees_planted=int(current_user.total_co2_saved // GOAL_CO2))

@app.route('/consumer/redeem')
@login_required
def redeem():
    vendor_offers = db.session.query(Offer, Vendor.business_name).join(Vendor, Offer.vendor_id == Vendor.id).filter(Offer.status == 'active').all()
    return render_template('redeem.html', user=current_user, mock_rewards=MOCK_REWARDS_DB, vendor_offers=vendor_offers)

@app.route('/api/consumer/redeem-reward', methods=['POST'])
@login_required
def api_redeem_reward():
    reward_id = request.json.get('reward_id') 
    reward_cost = 0
    if reward_id.startswith('gov_'):
        reward_cost = MOCK_REWARDS_DB.get(reward_id, {}).get('cost', 0)
    elif reward_id.startswith('offer_'):
        offer = Offer.query.get(int(reward_id.split('_')[1]))
        if offer and offer.status == 'active': reward_cost = offer.mosscoin_cost
    if current_user.mosscoin_balance < reward_cost: return jsonify({'error': 'Not enough MossCoins!'}), 400
    try:
        current_user.mosscoin_balance -= reward_cost
        db.session.commit()
        return jsonify({'message': 'Reward redeemed!', 'new_balance': current_user.mosscoin_balance}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/consumer/eco_tips')
@login_required
def eco_tips(): return render_template('eco_tips.html')

@app.route('/consumer/eco_advisor')
@login_required
def eco_advisor(): return render_template('eco_advisor.html')

@app.route('/consumer/refer_and_earn')
@login_required
def refer_and_earn():
    return render_template('refer_and_earn.html', referral_code=f"{current_user.fullname.split(' ')[0].upper()[:5]}{current_user.id * 3}")

@app.route('/consumer/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST' and request.form.get('form_name') == 'update_profile':
        try:
            current_user.fullname = request.form.get('fullname')
            current_user.email = request.form.get('email')
            current_user.phone = request.form.get('phone')
            db.session.commit()
            flash('Profile updated successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}')
        return redirect(url_for('settings'))
    return render_template('settings.html', user=current_user)

@app.route('/api/consumer/change-password', methods=['POST'])
@login_required
def api_change_password():
    data = request.json
    if not current_user.check_password(data.get('old_password')): return jsonify({'error': 'Old password is not correct.'}), 400
    try:
        current_user.set_password(data.get('new_password'))
        db.session.commit()
        return jsonify({'message': 'Password updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- Vendor Routes ---
@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        vendor = Vendor.query.filter_by(email=request.form.get('email')).first()
        if vendor and vendor.check_password(request.form.get('password')):
            session['vendor_id'] = vendor.id
            return redirect(url_for('vendor_dashboard'))
        else:
            flash('Invalid email or password. Please try again.')
            return redirect(url_for('vendor_login'))
    return render_template('vendor_login.html')

@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        if request.form.get('password') != request.form.get('confirm-password'):
            flash("Passwords do not match.")
            return redirect(url_for('vendor_register'))
        if Vendor.query.filter_by(email=request.form.get('email')).first():
            flash("An account with this email already exists.")
            return redirect(url_for('vendor_register'))
        try:
            new_vendor = Vendor(
                business_name=request.form.get('business-name'), contact_name=request.form.get('contact-name'),
                email=request.form.get('email'), mobile=request.form.get('mobile'),
                udyam_id=request.form.get('udyam-id'), address=request.form.get('address')
            )
            new_vendor.set_password(request.form.get('password'))
            db.session.add(new_vendor)
            db.session.commit()
            flash("Vendor registered successfully! Please log in.")
            return redirect(url_for('vendor_login'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}")
            return redirect(url_for('vendor_register'))
    return render_template('vendor_register.html')

@app.route('/vendor/dashboard')
def vendor_dashboard():
    if 'vendor_id' not in session: return redirect(url_for('vendor_login'))
    vendor = Vendor.query.get(session['vendor_id'])
    if not vendor: return redirect(url_for('vendor_login'))
    low_stock_items = Item.query.filter(Item.vendor_id == session['vendor_id'], Item.stock <= 10).order_by(Item.stock.asc()).all()
    return render_template('vendor_dashboard.html', vendor=vendor, low_stock_items=low_stock_items)

@app.route('/vendor/logout')
def vendor_logout():
    session.pop('vendor_id', None)
    return redirect(url_for('vendor_login'))

@app.route('/vendor/manage_items')
def manage_items():
    if 'vendor_id' not in session: return redirect(url_for('vendor_login'))
    vendor_items = Item.query.filter_by(vendor_id=session['vendor_id']).all()
    item_database_with_savings = {}
    for category, items in CARBON_FOOTPRINT_DB.items():
        item_database_with_savings[category] = {}
        for name, data in items.items():
            item_database_with_savings[category][name] = data['unsustainable_kg'] - data['sustainable_kg']
    return render_template('manage_items.html', items=vendor_items, item_database=item_database_with_savings)

@app.route('/api/vendor/add-item', methods=['POST'])
def add_item():
    if 'vendor_id' not in session: return jsonify({'error': 'Not authorized'}), 401
    data = request.json
    item_name_from_form = data['name']
    
    carbon_saved = 0.0
    for category, items in CARBON_FOOTPRINT_DB.items():
        for name, values in items.items():
            if name.lower() == item_name_from_form.lower():
                carbon_saved = values['unsustainable_kg'] - values['sustainable_kg']
                break

    try:
        # --- WEB3 INTEGRATION ---
        try:
            algod_client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")
            secret_phrase = "sail just ten armor bullet wasp engage zoo famous price despair struggle route day music meadow wheel tank nest sketch snap pumpkin area abstract sauce"
            secret_key = mnemonic.to_private_key(secret_phrase)
            sender_address = account.address_from_private_key(secret_key) 
            
            app_address = get_application_address(755790958)
            carbon_proof = f"MossPay Verified: {item_name_from_form} saves {carbon_saved}kg CO2"
            
            txn = transaction.PaymentTxn(sender_address, algod_client.suggested_params(), app_address, 0, note=carbon_proof.encode())
            txid = algod_client.send_transaction(txn.sign(secret_key))
            print(f"🟢 WEB3 SUCCESS! Data logged to Algorand App 755790958. TXID: {txid}")
        except Exception as e:
            print(f"🟡 Web3 Notice: {e}")

        new_item = Item(
            name=item_name_from_form, price=float(data['price']), unit=data['unit'],
            stock=int(data['stock']), carbon_saved_kg=carbon_saved, vendor_id=session['vendor_id']
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'id': new_item.id, 'name': new_item.name, 'price': new_item.price, 'unit': new_item.unit, 'stock': new_item.stock, 'carbon_saved_kg': new_item.carbon_saved_kg}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/vendor/generate_bill')
def generate_bill():
    if 'vendor_id' not in session: return redirect(url_for('vendor_login'))
    return render_template('generate_bill.html', items=Item.query.filter(Item.vendor_id == session['vendor_id'], Item.stock > 0).all())

# --- THE BULLETPROOF UNIFIED B2C AND B2B BILLING SYSTEM ---
@app.route('/api/vendor/send-bill-to-phone', methods=['POST'])
def send_bill_to_phone():
    if 'vendor_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401
    
    seller_id = session['vendor_id']
    data = request.json
    
    # Strip any invisible spaces from the phone number
    phone_number = data.get('phone', '').strip()
    cart = data.get('cart') 
    
    if not phone_number or not cart:
        return jsonify({'error': 'Missing phone number or items.'}), 400

    # Safety Check: Did the seller accidentally enter their own number?
    seller_vendor = Vendor.query.get(seller_id)
    if seller_vendor.mobile.strip() == phone_number:
        return jsonify({'error': 'You cannot generate a bill for yourself! Please enter a different phone number.'}), 400
        
    # 1. First, check if the phone belongs to a Consumer (User)
    customer = User.query.filter_by(phone=phone_number).first()
    
    # 2. If not a consumer, look for ANOTHER Vendor with this number
    buyer_vendor = Vendor.query.filter(Vendor.mobile == phone_number, Vendor.id != seller_id).first()
    
    if not customer and not buyer_vendor:
        return jsonify({'error': f'No MossPay account found with phone number {phone_number}.'}), 404

    # 3. Pre-calculate totals and check stock before committing anything to DB
    total_amount = 0
    total_carbon = 0
    items_to_process = []
    
    with db.session.no_autoflush:
        for cart_item in cart:
            item_id = cart_item['id']
            quantity = int(cart_item['quantity'])
            item_in_db = Item.query.get(item_id)
            
            if not item_in_db:
                return jsonify({'error': f'Item ID {item_id} not found.'}), 400
            if item_in_db.stock < quantity:
                return jsonify({'error': f'Not enough stock for {item_in_db.name}. Only {item_in_db.stock} left.'}), 400
                
            total_amount += item_in_db.price * quantity
            total_carbon += item_in_db.carbon_saved_kg * quantity
            items_to_process.append({'db_item': item_in_db, 'qty': quantity})

    try:
        if customer:
            # ==========================================
            # 🟢 B2C LOGIC (Business to Consumer Sale)
            # ==========================================
            mosscoins = int(total_carbon * 10)
            new_bill = Bill(
                vendor_id=seller_id, customer_id=customer.id,
                total_amount=total_amount, total_carbon_saved=total_carbon,
                mosscoins_to_award=mosscoins, status='pending'
            )
            db.session.add(new_bill)
            db.session.flush() 
            
            for item_data in items_to_process:
                db_item = item_data['db_item']
                qty = item_data['qty']
                bill_item_entry = BillItem(
                    bill_id=new_bill.id, item_id=db_item.id, quantity=qty,
                    price_at_sale=db_item.price, carbon_at_sale=db_item.carbon_saved_kg
                )
                db.session.add(bill_item_entry)
                db_item.stock -= qty # Deduct stock
            
            db.session.commit()
            return jsonify({'message': f'Bill successfully sent to customer {customer.fullname}!', 'bill_id': new_bill.id}), 201
            
        elif buyer_vendor:
            # ==========================================
            # 🟢 B2B LOGIC (Manual Wholesale Billing)
            # ==========================================
            distance_km = calculate_shop_distance(buyer_vendor.address, seller_vendor.address)
            
            for item_data in items_to_process:
                db_item = item_data['db_item']
                qty = item_data['qty']
                
                # Deduct from seller
                db_item.stock -= qty
                
                # Add to buyer's inventory magically
                buyer_inventory_item = Item.query.filter_by(vendor_id=buyer_vendor.id, name=db_item.name).first()
                if buyer_inventory_item:
                    buyer_inventory_item.stock += qty
                else:
                    new_inventory_item = Item(
                        name=db_item.name, price=db_item.price, unit=db_item.unit,
                        stock=qty, carbon_saved_kg=db_item.carbon_saved_kg, vendor_id=buyer_vendor.id
                    )
                    db.session.add(new_inventory_item)
                    
                # Log in B2BOrder history table
                b2b_order = B2BOrder(
                    buyer_id=buyer_vendor.id, seller_id=seller_id,
                    item_name=db_item.name, quantity=qty,
                    price_paid=(db_item.price * qty), carbon_saved=(db_item.carbon_saved_kg * qty)
                )
                db.session.add(b2b_order)
                
                # 🔗 Web3 Algorand Stamp!
                try:
                    algod_client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")
                    secret_phrase = "sail just ten armor bullet wasp engage zoo famous price despair struggle route day music meadow wheel tank nest sketch snap pumpkin area abstract sauce"
                    secret_key = mnemonic.to_private_key(secret_phrase)
                    sender_address = account.address_from_private_key(secret_key)
                    
                    trade_proof = f"POS B2B: Vendor {buyer_vendor.id} bought {qty}x {db_item.name}. Dist: {distance_km}km."
                    txn = transaction.PaymentTxn(sender_address, algod_client.suggested_params(), get_application_address(755790958), 0, note=trade_proof.encode())
                    algod_client.send_transaction(txn.sign(secret_key))
                    print(f"🟢 POS WEB3 SUCCESS! B2B Trade logged. Distance: {distance_km}km")
                except Exception as e:
                    print(f"🟡 Web3 Notice: {e}")
            
            db.session.commit()
            return jsonify({'message': f'Wholesale POS complete! Items sent to {buyer_vendor.business_name}.'}), 201
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/vendor/manage_profile', methods=['GET', 'POST'])
def manage_profile():
    if 'vendor_id' not in session: return redirect(url_for('vendor_login'))
    vendor = Vendor.query.get(session['vendor_id'])
    if request.method == 'POST':
        vendor.business_name = request.form.get('business_name')
        vendor.contact_name = request.form.get('contact_name')
        vendor.mobile = request.form.get('mobile')
        vendor.address = request.form.get('address')
        vendor.shop_category = request.form.get('shop_category')
        vendor.description = request.form.get('description')
        try:
            db.session.commit()
            flash('Profile updated successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}')
        return redirect(url_for('manage_profile'))
    return render_template('manage_profile.html', vendor=vendor)

@app.route('/vendor/manage_offers', methods=['GET', 'POST'])
def manage_offers():
    if 'vendor_id' not in session: return redirect(url_for('vendor_login'))
    if request.method == 'POST':
        try:
            db.session.add(Offer(vendor_id=session['vendor_id'], title=request.form.get('title'), description=request.form.get('description'), mosscoin_cost=int(request.form.get('mosscoin_cost'))))
            db.session.commit()
            flash('New offer created successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating offer: {e}')
        return redirect(url_for('manage_offers'))
    return render_template('manage_offers.html', offers=Offer.query.filter_by(vendor_id=session['vendor_id'], status='active').all())

@app.route('/vendor/transaction_history')
def transaction_history():
    if 'vendor_id' not in session: return redirect(url_for('vendor_login'))
    transactions = db.session.query(Bill, User.fullname).join(User, Bill.customer_id == User.id).filter(Bill.vendor_id == session['vendor_id']).order_by(Bill.created_at.desc()).all()
    return render_template('transaction_history.html', transactions=transactions)

@app.route('/vendor/customer_insights')
def customer_insights():
    if 'vendor_id' not in session: return redirect(url_for('vendor_login'))
    return render_template('customer_insights.html')

@app.route('/vendor/settings', methods=['GET', 'POST'])
def vendor_settings():
    if 'vendor_id' not in session: return redirect(url_for('vendor_login'))
    vendor = Vendor.query.get(session['vendor_id'])
    if request.method == 'POST':
        try:
            vendor.contact_name = request.form.get('contact_name')
            vendor.email = request.form.get('email')
            db.session.commit()
            flash('Account details updated successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}')
        return redirect(url_for('vendor_settings'))
    return render_template('vendor_settings.html', vendor=vendor)

@app.route('/vendor/my_subscription')
def my_subscription():
    if 'vendor_id' not in session: return redirect(url_for('vendor_login'))
    return render_template('my_subscription.html', current_plan="MossPay Basic")

# --- B2B MARKET ROUTES ---
@app.route('/b2b_market')
def b2b_market():
    if 'vendor_id' not in session:
        flash('You must be logged in as a vendor to view the B2B market.')
        return redirect(url_for('vendor_login'))

    all_vendors = Vendor.query.all()
    vendor_data = []
    for vendor in all_vendors:
        items_list = []
        vendor_items = Item.query.filter_by(vendor_id=vendor.id).all()
        for item in vendor_items:
            items_list.append({
                "id": item.id,
                "name": item.name,
                "stock": item.stock, 
                "unit": item.unit,
                "price": item.price,
                "carbon_saved_kg": item.carbon_saved_kg
            })
        vendor_data.append({
            "vendor": {
                "id": vendor.id,
                "business_name": vendor.business_name,
                "shop_category": vendor.shop_category or 'General',
                "contact_name": vendor.contact_name,
                "mobile": vendor.mobile,
                "address": vendor.address,
                "description": vendor.description or 'A registered MossPay sustainable vendor.'
            },
            "items": items_list
        })
    return render_template('b2b_market.html', vendor_data=vendor_data)

@app.route('/api/b2b/buy', methods=['POST'])
def b2b_buy():
    if 'vendor_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    buyer_id = session['vendor_id']
    data = request.json
    seller_item = Item.query.get(data.get('item_id'))
    buy_qty = int(data.get('quantity', 1))
    
    if not seller_item or seller_item.stock < buy_qty:
        return jsonify({'error': 'Not enough stock'}), 400
    if seller_item.vendor_id == buyer_id:
        return jsonify({'error': 'You cannot buy your own item!'}), 400
        
    buyer = Vendor.query.get(buyer_id)
    seller = Vendor.query.get(seller_item.vendor_id)

    # 1. Deduct stock from Seller
    seller_item.stock -= buy_qty
    
    # 2. Add to Buyer's Inventory
    buyer_item = Item.query.filter_by(vendor_id=buyer_id, name=seller_item.name).first()
    if buyer_item:
        buyer_item.stock += buy_qty
    else:
        buyer_item = Item(
            name=seller_item.name, price=seller_item.price, unit=seller_item.unit,
            stock=buy_qty, carbon_saved_kg=seller_item.carbon_saved_kg, vendor_id=buyer_id
        )
        db.session.add(buyer_item)
        
    # 3. Log History
    b2b_order = B2BOrder(
        buyer_id=buyer_id, seller_id=seller_item.vendor_id, item_name=seller_item.name, 
        quantity=buy_qty, price_paid=(seller_item.price * buy_qty), carbon_saved=(seller_item.carbon_saved_kg * buy_qty)
    )
    db.session.add(b2b_order)
    
    # 4. Web3 Zero-Cost Stamp with Geopy Transport Distance!
    try:
        distance_km = calculate_shop_distance(buyer.address, seller.address)
        
        algod_client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")
        secret_phrase = "sail just ten armor bullet wasp engage zoo famous price despair struggle route day music meadow wheel tank nest sketch snap pumpkin area abstract sauce"
        secret_key = mnemonic.to_private_key(secret_phrase)
        sender_address = account.address_from_private_key(secret_key)
        
        trade_proof = f"B2B Trade: Vendor {buyer_id} bought {buy_qty}x {seller_item.name}. Supply chain distance: {distance_km} km."
        txn = transaction.PaymentTxn(sender_address, algod_client.suggested_params(), get_application_address(755790958), 0, note=trade_proof.encode())
        algod_client.send_transaction(txn.sign(secret_key))
        print(f"🟢 B2B WEB3 SUCCESS! Trade logged. Distance: {distance_km}km")
    except Exception as e:
        print(f"🟡 Web3 Notice: {e}")

    db.session.commit()
    return jsonify({'message': 'Purchase successful! Item added to your inventory.'}), 200

# --- Main ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)