"""
from .models import User,Category,Product,Cart
from . import views
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify
from . import db
 
 #add to cart
@views.route('/cart/add',methods=['POST'])
#@jwt_required
def add_to_cart():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        product = Product.query.get(data['productID'])
        quantity = data.get('quantity',1)
    
        if not product or product.quantity < data['quantity']:
            return jsonify({"msg": "Invalid product or insufficient stock"}), 400
        cart_item = Cart.query.filter_by(userId=user_id,
                                         productID=product.productID).first() 
    
        if cart_item:
             cart_item.quantity += data['quantity']
        else:
            cart_item = Cart(userId=user_id, 
                         productID=product.productID, 
                         quantity=data['quantity'])
            db.session.add(cart_item)
            
        product.quantity-= quantity 

        db.session.commit()
        return jsonify({"msg": "Item added to cart"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error adding item to cart", "error": str(e)}), 500
   
"""
