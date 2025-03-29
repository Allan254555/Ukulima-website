from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from .models import db, Orders, OrderItem, Product, Cart, User
from flask_jwt_extended import jwt_required, get_jwt_identity

orders = Blueprint("orders", __name__)

#Order creation endpoint
@orders.route('/order', methods=['POST'])
@jwt_required()
def create_order():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    data = request.get_json()
    order_items = data.get('order_items', [])#For direct orders
        
    if not order_items:
        #If no items are provided fetch from cart
        cart_items = Cart.query.filter_by(user_id=user.id).all()
        
        if not cart_items:
            return jsonify({"msg": "No items to order"}), 400
        
        order_items = [{"product_id": item.product_id, "quantity": item.quantity} for item in cart_items]
        
    total_amount = 0
    order_item_list = []  
    
    for item in order_items:
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({"msg": f"Product ID{item.get("product_id")} not found"}), 404
        
        if product.quantity < item('quantity',0):
            return jsonify({"msg": "Insufficient stock"}), 400
        
        # Calculate total amount
        sub_total += product.price * item['quantity']
        total_amount += sub_total
        
        order_item = OrderItem(
            productID=product.productsID,
            quantity=item['quantity'],
            sub_total=sub_total
        )
        
        order_item_list.append(order_item)
        
    # Create new order
    new_order=Orders(
        user_id=user.id,
        total_amount=total_amount,
        order_status='Pending',  
    )
    db.session.add(new_order)
    db.session.commit()
    
    #save order items
    for order_item in order_item_list:
        order_item.orderID = new_order.orderID
        db.session.add(order_item)
        
    # If order is from cart, clear cart
    if not data.get('items', []):  # Only clear cart if ordering from cart
        Cart.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
    return jsonify({"msg": "Order created successfully", "order_id": new_order.orderID}), 201
#Process order
@orders.route('/order/process/<int:order_id>', methods=['POST'])
@jwt_required()
def process_order(order_id):
    order=Orders.query.get(order_id)
    if not order:
        return jsonify({"msg":"Order not found"}),404
    
    if order.order_status != "Pending":
        return jsonify({"msg":"Order cannot be processed"}),400  
    
    #Deduct stock for each order item in the order
    for item in order.items:
        product = Product.query.get(item.productID)
        if product and product.quantity >= item.quantity:
            product.quantity -= item.quantity
            if product.quantity < 0:
                return jsonify({"msg":f"Insufficient stock for {product.productName}"}),400
    order.order_status = "Processing"
    db.session.commit()
    return jsonify({"msg":"Order processed successfully"}),200

#Cancel order
@orders.route('/order/cancel/<int:order_id>', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    order = Orders.query.get(order_id)
    if not order:
        return jsonify({"msg":"Order not found"}),404
    
    if order.order_status == "Cancelled":
        return jsonify({"msg":"Order already cancelled"}),400
    
    # Restock items in the order
    for item in order.items:
        product = Product.query.get(item.productID)
        if product:
            product.quantity += item.quantity
    
    order.order_status = "Cancelled"
    db.session.commit()
    return jsonify({"msg":"Order cancelled successfully"}),200


    
    
    