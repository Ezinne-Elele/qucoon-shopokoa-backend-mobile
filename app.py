from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os
from datetime import datetime
import secrets

app = Flask(__name__)
CORS(app)

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'shopokoa')

try:
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    products_collection = db['products']
    users_collection = db['users']
    cart_collection = db['cart']
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'mobile-api',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Mobile app version check
@app.route('/api/mobile/version', methods=['GET'])
def check_version():
    return jsonify({
        'version': '1.0.0',
        'minVersion': '1.0.0',
        'updateRequired': False,
        'features': ['products', 'cart', 'orders', 'profile']
    }), 200

# User authentication (dummy)
@app.route('/api/mobile/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Dummy authentication - accept any credentials
        user = {
            'userId': secrets.token_hex(8),
            'email': email,
            'name': email.split('@')[0].capitalize(),
            'token': secrets.token_urlsafe(32)
        }
        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get products for mobile
@app.route('/api/mobile/products', methods=['GET'])
def get_mobile_products():
    try:
        category = request.args.get('category', None)
        query = {'category': category} if category else {}
        
        products = list(products_collection.find(query, {'_id': 0}))
        if not products:
            # Return dummy data if database is empty
            products = [
                {
                    'id': '1',
                    'name': 'Laptop Pro',
                    'description': 'High-performance laptop for professionals',
                    'price': 1299.99,
                    'category': 'Electronics',
                    'stock': 15,
                    'image': 'https://via.placeholder.com/300x300?text=Laptop',
                    'rating': 4.5
                },
                {
                    'id': '2',
                    'name': 'Wireless Mouse',
                    'description': 'Ergonomic wireless mouse',
                    'price': 29.99,
                    'category': 'Accessories',
                    'stock': 50,
                    'image': 'https://via.placeholder.com/300x300?text=Mouse',
                    'rating': 4.2
                },
                {
                    'id': '3',
                    'name': 'USB-C Hub',
                    'description': '7-in-1 USB-C hub adapter',
                    'price': 49.99,
                    'category': 'Accessories',
                    'stock': 30,
                    'image': 'https://via.placeholder.com/300x300?text=Hub',
                    'rating': 4.7
                },
                {
                    'id': '4',
                    'name': 'Smartphone X',
                    'description': 'Latest flagship smartphone',
                    'price': 999.99,
                    'category': 'Electronics',
                    'stock': 25,
                    'image': 'https://via.placeholder.com/300x300?text=Phone',
                    'rating': 4.8
                }
            ]
        return jsonify(products), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add to cart
@app.route('/api/mobile/cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.json
        cart_item = {
            'userId': data.get('userId'),
            'productId': data.get('productId'),
            'quantity': data.get('quantity', 1),
            'addedAt': datetime.utcnow().isoformat()
        }
        cart_collection.insert_one(cart_item)
        return jsonify({'message': 'Item added to cart'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get cart items
@app.route('/api/mobile/cart/<user_id>', methods=['GET'])
def get_cart(user_id):
    try:
        cart_items = list(cart_collection.find({'userId': user_id}, {'_id': 0}))
        return jsonify(cart_items), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get featured products
@app.route('/api/mobile/featured', methods=['GET'])
def get_featured():
    try:
        featured = [
            {
                'id': '1',
                'name': 'Laptop Pro',
                'price': 1299.99,
                'image': 'https://via.placeholder.com/300x300?text=Laptop',
                'badge': 'Best Seller'
            },
            {
                'id': '4',
                'name': 'Smartphone X',
                'price': 999.99,
                'image': 'https://via.placeholder.com/300x300?text=Phone',
                'badge': 'New Arrival'
            }
        ]
        return jsonify(featured), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)