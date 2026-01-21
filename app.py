from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import random
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'rentique_secret_key_change_this_later'

# MongoDB Connection
# Atlas Connection
client = MongoClient('mongodb+srv://vishakhkt:vishakh2003@cluster0.hkgog.mongodb.net/aurawear?retryWrites=true&w=majority')
db = client['aurawear_db']
users_collection = db['users']
items_collection = db['items']
bookings_collection = db['bookings']

# --- Helper Functions ---
def generate_id():
    """Generates a unique integer ID based on timestamp."""
    return int(time.time() * 1000) % 1000000000

# --- Routes ---

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    # User Entity: email, name, password, role, user_id
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    # phone is not in dictionary but might be useful, keeping it optional or removing if strict
    phone = request.form.get('phone') 

    if users_collection.find_one({'email': email}):
        flash('Email already registered!')
        return redirect(url_for('index'))

    user_id = generate_id()

    # In production, hash passwords!
    users_collection.insert_one({
        'user_id': user_id,
        'name': name,
        'email': email,
        'password': password,
        'role': 'User', # Dictionary says "Defines user type (Admin/User)"
        'phone': phone # Keeping extra field just in case
    })
    
    # Auto login
    session['user'] = email
    session['user_id'] = user_id
    session['role'] = 'User'
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    username_or_email = request.form.get('username') # Form field name is username
    password = request.form.get('password')

    # Admin check - strict dictionary compliance would have an Admin table
    # But for now we can simulate "Admins" via the User table or hardcode if they exist there
    # Let's check the database first
    
    user = users_collection.find_one({'$or': [{'email': username_or_email}, {'name': username_or_email}]})
    
    # If explicit admin credentials used and not in DB, we can manually handle or just rely on DB
    if username_or_email == 'admin@aurawear.com' and password == 'admin123':
        session['user'] = 'admin@aurawear.com'
        session['role'] = 'Admin'
        session['user_id'] = 1 # Static ID for superadmin
        return redirect(url_for('admin'))

    if user and user['password'] == password:
        session['user'] = user['email']
        session['user_id'] = user.get('user_id')
        session['role'] = user.get('role', 'User')
        
        if session['role'] == 'Admin':
            return redirect(url_for('admin'))
        return redirect(url_for('home'))
    
    flash('Invalid credentials')
    return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    query = request.args.get('q')
    if query:
        # Simple regex search
        items = list(items_collection.find({'name': {'$regex': query, '$options': 'i'}}))
    else:
        items = list(items_collection.find())
    
    return render_template('home.html', items=items)

@app.route('/category/<category_name>')
def category_page(category_name):
    if 'user' not in session:
        return redirect(url_for('index'))
    
    # Flexible regex search to find "Women" in "Women - Dress" etc.
    items = list(items_collection.find({'category': {'$regex': category_name, '$options': 'i'}}))
    
    return render_template('category.html', items=items, category_name=category_name)

@app.route('/product/<item_id>')
def product_detail(item_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    
    # Try finding by outfit_id (int) or _id (ObjectId) to be safe with old data
    try:
        query_id = int(item_id)
        item = items_collection.find_one({'outfit_id': query_id})
    except ValueError:
        item = items_collection.find_one({'_id': ObjectId(item_id)})
        
    if not item:
        return redirect(url_for('home'))
        
    return render_template('product_detail.html', item=item)

@app.route('/book/<item_id>', methods=['POST'])
def book_item(item_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    
    # Retrieve Item
    try:
        query_id = int(item_id)
        item = items_collection.find_one({'outfit_id': query_id})
    except ValueError:
        item = items_collection.find_one({'_id': ObjectId(item_id)})

    if not item:
        return redirect(url_for('home'))

    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    
    # Calculate days
    try:
        d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
        d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
        delta = d2 - d1
        days = max(1, delta.days) # Minimum 1 day
    except:
        days = 1
        d1 = datetime.now() # Fallback
        
    total_amount = float(item['price']) * days
    
    rental_id = generate_id()
    user_id = session.get('user_id')
    
    # Fallback if old user without user_id
    if not user_id: 
        user_rec = users_collection.find_one({'email': session['user']})
        if user_rec:
            user_id = user_rec.get('user_id', 0)
    
    # Dictionary: rental_id, user_id, outfit_id, rental_date, return_date, total_amount
    bookings_collection.insert_one({
        'rental_id': rental_id,
        'user_id': user_id,
        'outfit_id': item.get('outfit_id', str(item['_id'])), # Use outfit_id if avail
        'rental_date': start_date_str,
        'return_date': end_date_str,
        'total_amount': total_amount,
        # Keeping extra fields for UI display ease, though strict dict doesn't specify them
        'item_name': item['name'],
        'image': item.get('image'),
        'status': 'Pending'
    })
    
    flash('Your rental booked successfully!')
    return redirect(url_for('my_rentals'))

@app.route('/my_rentals')
def my_rentals():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    # Get user bookings (sort by specific field if needed, currently just grabbing all)
    user_id = session.get('user_id')
    if user_id:
        user_bookings = list(bookings_collection.find({'user_id': user_id}).sort('rental_date', -1))
    else:
        # Fallback for old data
        user_bookings = list(bookings_collection.find({'user_email': session['user']}).sort('rental_date', -1))
    
    return render_template('my_rentals.html', bookings=user_bookings)

@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect(url_for('index'))
    # Allow strict admin role check
    if session.get('role') != 'Admin' and session.get('role') != 'admin':
         return redirect(url_for('index'))
    
    items = list(items_collection.find())
    return render_template('admin.html', items=items)

# --- Admin Operations ---

@app.route('/add_item', methods=['POST'])
def add_item():
    if 'user' not in session:
        return redirect(url_for('index'))
    if session.get('role') != 'Admin' and session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    # Outfit Entity: availability, description, image, outfit_id, price, name
    
    outfit_id = generate_id()
    
    items_collection.insert_one({
        'outfit_id': outfit_id,
        'name': request.form.get('name'),
        'category': request.form.get('category'), # Keeping for flow
        'price': float(request.form.get('price')),
        'description': request.form.get('description'),
        'image': request.form.get('image'), # was image_url
        'availability': True, # Default
        'pickup_date': request.form.get('pickup_date') # Keeping usage
    })
    return redirect(url_for('admin'))

@app.route('/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    if 'user' not in session:
         return redirect(url_for('index'))
    if session.get('role') != 'Admin' and session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    try:
        query_id = int(item_id)
        items_collection.delete_one({'outfit_id': query_id})
    except ValueError:
        items_collection.delete_one({'_id': ObjectId(item_id)})

    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
