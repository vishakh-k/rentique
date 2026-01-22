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
    if username_or_email == 'admin@rentique.com' and password == 'admin123':
        session['user'] = 'admin@rentique.com'
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
        # Find item that is available (though availability check should be done)
        # If we want to strictly allow only if available:
        item = items_collection.find_one({'outfit_id': query_id})
    except ValueError:
        item = items_collection.find_one({'_id': ObjectId(item_id)})

    if not item:
        return redirect(url_for('home'))
    
    # Check availability again to be safe
    if not item.get('availability', True): # Default to True if key missing, but if False prevent
         flash('Sorry, this item is currently unavailable.')
         return redirect(url_for('product_detail', item_id=item_id))

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
    
    # Insert Booking
    bookings_collection.insert_one({
        'rental_id': rental_id,
        'user_id': user_id,
        'outfit_id': item.get('outfit_id', str(item['_id'])),
        'rental_date': start_date_str,
        'return_date': end_date_str,
        'total_amount': total_amount,
        'item_name': item['name'],
        'image': item.get('image'),
        'status': 'Pending',
        'created_at': datetime.now(), # Store creation time for cancellation logic
        'payment_mode': 'COD'
    })
    
    # Update Item Availability to False so no one else can book it
    if item.get('outfit_id'):
         items_collection.update_one({'outfit_id': item['outfit_id']}, {'$set': {'availability': False}})
    else:
         items_collection.update_one({'_id': item['_id']}, {'$set': {'availability': False}})

    flash('Your rental booked successfully! Payment: Cash on Delivery.')
    return redirect(url_for('my_rentals'))

@app.route('/cancel_rental/<rental_id>', methods=['POST'])
def cancel_rental(rental_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    
    try:
        r_id = int(rental_id)
        booking = bookings_collection.find_one({'rental_id': r_id})
    except:
        return redirect(url_for('my_rentals'))
    
    if not booking:
        flash('Booking not found.')
        return redirect(url_for('my_rentals'))
        
    # Check time limit (2 hours)
    created_at = booking.get('created_at')
    if created_at:
        # Ensure created_at is a datetime object (pymongo usually handles this if inserted as datetime)
        time_diff = datetime.now() - created_at
        hours_passed = time_diff.total_seconds() / 3600
        
        if hours_passed > 2:
            flash('Cancellation period (2 hours) has expired.')
            return redirect(url_for('my_rentals'))
    else:
        # If legacy record without timestamp, maybe allow or disallow. Let's allow for now or disallow.
        # Safe choice: Allow if status is Pending, but for strict 2hr rule, maybe disallow.
        # Let's assume new bookings only have created_at.
        pass

    # Update Booking Status
    bookings_collection.update_one({'rental_id': r_id}, {'$set': {'status': 'Cancelled'}})
    
    # Make item available again
    outfit_id = booking.get('outfit_id')
    if outfit_id:
        try:
            # Try as integer ID first
            oid = int(outfit_id)
            result = items_collection.update_one({'outfit_id': oid}, {'$set': {'availability': True}})
            # If no document modified, maybe it's using _id or something else, but strictly our add_item uses int.
            # But let's be safe for legacy/mixed data.
            if result.modified_count == 0:
                 # Check if it was an ObjectId string?
                 pass
        except ValueError:
            # If convert to int fails, it might be an ObjectId string
            try:
                items_collection.update_one({'_id': ObjectId(outfit_id)}, {'$set': {'availability': True}})
            except:
                pass

    flash('Rental cancelled successfully. Item is now available for others.')
    return redirect(url_for('my_rentals'))

@app.route('/delete_rental/<rental_id>', methods=['POST'])
def delete_rental(rental_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    
    try:
        r_id = int(rental_id)
        booking = bookings_collection.find_one({'rental_id': r_id})
    except:
        return redirect(url_for('my_rentals'))
    
    if booking:
        # If deleting an active/pending rental, we must release the item item
        if booking.get('status') != 'Cancelled':
             outfit_id = booking.get('outfit_id')
             if outfit_id:
                try:
                    oid = int(outfit_id)
                    items_collection.update_one({'outfit_id': oid}, {'$set': {'availability': True}})
                except:
                     try:
                        items_collection.update_one({'_id': ObjectId(outfit_id)}, {'$set': {'availability': True}})
                     except:
                        pass
        
        # Remove from DB
        bookings_collection.delete_one({'rental_id': r_id})
        flash('Rental record deleted successfully.')
    
    return redirect(url_for('my_rentals'))

@app.route('/my_rentals')
def my_rentals():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    user_id = session.get('user_id')
    if user_id:
        user_bookings = list(bookings_collection.find({'user_id': user_id}).sort('rental_date', -1))
    else:
        user_bookings = list(bookings_collection.find({'user_email': session['user']}).sort('rental_date', -1))
    
    # Pass current time for template comparison if needed, though backend handles the action
    return render_template('my_rentals.html', bookings=user_bookings, now=datetime.now(), timedelta=lambda x: x.total_seconds()/3600)

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
