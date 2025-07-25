from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import json
import os
from pathlib import Path

app = Flask(__name__)

# File paths
DATA_DIR = Path(__file__).parent / 'data'
DATA_FILE = DATA_DIR / 'products.json'
SETTINGS_FILE = DATA_DIR / 'settings.json'

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Default settings
DEFAULT_SETTINGS = {
    'theme': 'light',
    'items_per_page': 10
}

def load_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, 'r') as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def load_products():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # Convert string dates back to date objects
            for product in data:
                product['manufacture_date'] = datetime.strptime(product['manufacture_date'], '%Y-%m-%d').date()
                product['expiry_date'] = datetime.strptime(product['expiry_date'], '%Y-%m-%d').date()
                product['added_date'] = datetime.strptime(product['added_date'], '%Y-%m-%d').date()
            return data
    return []

def save_products(products_list):
    # Convert date objects to strings for JSON serialization
    serializable_products = []
    for product in products_list:
        serialized = product.copy()
        serialized['manufacture_date'] = product['manufacture_date'].isoformat()
        serialized['expiry_date'] = product['expiry_date'].isoformat()
        serialized['added_date'] = product['added_date'].isoformat()
        serializable_products.append(serialized)
    
    with open(DATA_FILE, 'w') as f:
        json.dump(serializable_products, f, indent=2)

def calculate_urgency(expiry_date):
    today = datetime.now().date()
    days_remaining = (expiry_date - today).days
    
    if days_remaining < 0:
        return 'expired', f"Expired {-days_remaining} days ago"
    elif days_remaining == 0:
        return 'urgent', "Expires today!"
    elif days_remaining <= 7:
        return 'urgent', f"Expires in {days_remaining} days"
    elif days_remaining <= 30:
        return 'soon', f"Expires in {days_remaining} days"
    return 'normal', f"Expires in {days_remaining} days"

@app.route('/')
def index():
    settings = load_settings()
    search_query = request.args.get('search', '').lower()
    products_with_urgency = []
    products = load_products()
    
    for product in products:
        urgency, status_text = calculate_urgency(product['expiry_date'])
        product_copy = product.copy()
        product_copy.update({
            'urgency': urgency,
            'status_text': status_text,
            'expiry_formatted': product['expiry_date'].strftime('%d/%m/%Y'),
            'manufacture_formatted': product['manufacture_date'].strftime('%d/%m/%Y')
        })
        products_with_urgency.append(product_copy)
    
    # Filter products based on search query
    if search_query:
        products_with_urgency = [p for p in products_with_urgency 
                               if search_query in p['name'].lower()]
    
    # Sort by urgency and expiry date
    sorted_products = sorted(products_with_urgency, key=lambda x: (
        {'expired': 0, 'urgent': 1, 'soon': 2, 'normal': 3}[x['urgency']],
        x['expiry_date']
    ))
    
    return render_template('index.html', 
                         products=sorted_products, 
                         now=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                         total_products=len(products),
                         search_query=search_query,
                         settings=settings)

@app.route('/add', methods=['POST'])
def add_product():
    products = load_products()
    new_id = max((p['id'] for p in products), default=0) + 1
    
    product = {
        'id': new_id,
        'name': request.form['name'],
        'quantity': int(request.form['quantity']),
        'manufacture_date': datetime.strptime(request.form['manufacture_date'], '%Y-%m-%d').date(),
        'expiry_date': datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date(),
        'added_date': datetime.now().date()
    }
    
    products.append(product)
    save_products(products)
    return redirect('/')

@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    products = load_products()
    products = [p for p in products if p['id'] != product_id]
    save_products(products)
    return redirect('/')

@app.route('/update_quantity/<int:product_id>', methods=['POST'])
def update_quantity(product_id):
    products = load_products()
    new_quantity = int(request.form['quantity'])
    
    for product in products:
        if product['id'] == product_id:
            product['quantity'] = new_quantity
            break
    
    save_products(products)
    return redirect('/')

@app.route('/change_theme', methods=['POST'])
def change_theme():
    settings = load_settings()
    settings['theme'] = request.form['theme']
    save_settings(settings)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)