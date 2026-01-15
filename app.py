from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'rentique_secret_key_change_this_later'

# MongoDB Connection
# Atlas Connection
client = MongoClient('mongodb+srv://vishakhkt:vishakh2003@cluster0.hkgog.mongodb.net/aurawear?retryWrites=true&w=majority')
db = client['aurawear_db']
users_collection = db['users']
items_collection = db['items']

# --- Routes ---

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    # Simple registration
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')

    if users_collection.find_one({'email': email}):
        flash('Email already registered!')
        return redirect(url_for('index'))

    # In production, hash passwords!
    users_collection.insert_one({
        'name': name,
        'email': email,
        'password': password,
        'phone': phone,
        'role': 'customer' # Default role
    })
    
    # Auto login
    session['user'] = email
    session['role'] = 'customer'
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    username_or_email = request.form.get('username') # Form field name is username
    password = request.form.get('password')

    # Check for admin hardcoded (optional, or use DB)
    if username_or_email == 'admin@aurawear.com' and password == 'admin123':
        session['user'] = 'admin'
        session['role'] = 'admin'
        return redirect(url_for('admin'))

    user = users_collection.find_one({'$or': [{'email': username_or_email}, {'name': username_or_email}]})
    
    if user and user['password'] == password:
        session['user'] = user['email']
        session['role'] = user.get('role', 'customer')
        if session['role'] == 'admin':
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

@app.route('/admin')
def admin():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    items = list(items_collection.find())
    return render_template('admin.html', items=items)

# --- Admin Operations ---

@app.route('/add_item', methods=['POST'])
def add_item():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    items_collection.insert_one({
        'name': request.form.get('name'),
        'category': request.form.get('category'),
        'price': request.form.get('price'),
        'pickup_date': request.form.get('pickup_date'),
        'image_url': request.form.get('image_url')
    })
    return redirect(url_for('admin'))

@app.route('/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    items_collection.delete_one({'_id': ObjectId(item_id)})
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
