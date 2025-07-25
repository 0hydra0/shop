from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# In-memory database
products = []

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
    # Add urgency info to each product
    products_with_urgency = []
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
    
    # Sort by urgency and expiry date
    sorted_products = sorted(products_with_urgency, key=lambda x: (
        {'expired': 0, 'urgent': 1, 'soon': 2, 'normal': 3}[x['urgency']],
        x['expiry_date']
    ))
    
    return render_template('index.html', products=sorted_products, now=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

@app.route('/add', methods=['POST'])
def add_product():
    product = {
        'id': len(products) + 1,
        'name': request.form['name'],
        'quantity': int(request.form['quantity']),
        'manufacture_date': datetime.strptime(request.form['manufacture_date'], '%Y-%m-%d').date(),
        'expiry_date': datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date(),
        'added_date': datetime.now().date()
    }
    products.append(product)
    return redirect('/')

@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    global products
    products = [p for p in products if p['id'] != product_id]
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)