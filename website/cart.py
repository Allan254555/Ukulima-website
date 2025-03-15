from .models import User,Category,Product,Cart
from .views import views
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify
from . import db
 
 #add to cart
@views.route('/cart',methods=['POST'])
@jwt_required
def add_to_cart():
    data = request.get_json()
    user_id = get_jwt_identity()
    product = Product.query.get(data['productID'])
    
    if not product or product.quantity < data['quantity']:
        return jsonify({"msg": "Invalid product or insufficient stock"}), 400
    cart_item = Cart.query.filter_by(userId=user_id, productID=product.productID).first() 
    
    if cart_item:
        cart_item.quantity += data['quantity']
    else:
        cart_item = Cart(userId=user_id, 
                         productID=product.productID, 
                         quantity=data['quantity'])
        db.session.add(cart_item)

    db.session.commit()
    return jsonify({"msg": "Item added to cart"}), 201   

