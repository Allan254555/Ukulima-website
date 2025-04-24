from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from .models import db, Orders, OrderItem, Product, Cart, User
from flask_jwt_extended import jwt_required, get_jwt_identity

orders = Blueprint("orders", __name__)


#Order creation endpoint
@orders.route('/create_order', methods=['POST'])
@jwt_required()
def create_order():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    data = request.get_json()
    order_items = data.get('order_items')
    delivery_address = data.get('delivery_address')
   
    
    #For direct orders
    if not order_items and 'productsID' in data and 'quantity' in data:
        order_items = [{
            "productsID": data['productsID'],
            "quantity": data['quantity']
        }]
        
    if not order_items:
        #If no items are provided fetch from cart
        cart_items = Cart.query.filter_by(user_id=user.id).all()
        
        if not cart_items:
            return jsonify({"msg": "No items to order"}), 400
        
        order_items = [{"productsID": item.productID, "quantity": item.quantity} for item in cart_items]
        
    total_amount = 0
    order_item_list = []  
    
    try:
        for item in order_items:
            product = Product.query.get(item['productsID'])
            if not product:
                return jsonify({"msg": f"Product ID{item.get('productsID')} not found"}), 404
            
            if product.quantity < item.get('quantity',0):
                return jsonify({"msg": "Insufficient stock"}), 400
            
            # Calculate total amount
            sub_total = product.price * item['quantity']
            total_amount += sub_total
            
            order_item = OrderItem(
                productID=product.productsID,
                quantity=item['quantity'],
                sub_total=sub_total
            )
            
            order_item_list.append(order_item)
        delivery_fee = 150.00 if total_amount > 1500 else 0.00  # Example delivery fee logic
        # Calculate total amount including delivery fee    
        total_items_amount = total_amount + delivery_fee     
        # Create new order
        new_order=Orders(
            user_id=user.id,
            total_amount=total_items_amount,
            delivery_fee=delivery_fee,
            delivery_address=delivery_address,
            order_status='Unpaid',  
        )
        db.session.add(new_order)
        db.session.flush()  # Flush to get the orderID before commit
        
        #save order items
        for order_item in order_item_list:
            order_item.orderID = new_order.orderID
            db.session.add(order_item)
            
            #deduct stock
            product = Product.query.get(order_item.productID)
            product.quantity -= order_item.quantity
            
           
        # If order is from cart, clear cart
        if not data.get('order_items') and not data.get('productsID'):
        # Only clear cart if ordering from cart
            Cart.query.filter_by(user_id=user.id).delete()
           
        db.session.commit()
            
        return jsonify({"msg": "Order created successfully", "orderID": new_order.orderID}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error creating order", "error": str(e)}), 500


#Customer can view there own orders
@orders.route('/my_orders', methods =['GET'])
@jwt_required()
def get_my_orders():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({"msg":"User not found"}),404
    
    user_orders = Orders.query.filter_by(user_id=user.id).all()
    order_list = []
    for order in user_orders:
        items = [{
            "productName": item.product.productName,
            "quantity": item.quantity,
            "price": item.product.price,
            "sub_total": item.sub_total
        } for item in order.items]

        
        order_list.append({
            "orderID": order.orderID,
            "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "order_status": order.order_status,
            "total_amount": order.total_amount,
            "items": items
        })
        
    return jsonify({"orders": order_list}), 200
#Process order
@orders.route('/order/process/<int:orderID>', methods=['POST'])
@jwt_required()
def process_order(orderID):
    order=Orders.query.get(orderID)
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
"""
#Cancel order
@orders.route('/order/cancel/<int:orderID>', methods=['POST'])
@jwt_required()
def cancel_order(orderID):
    order = Orders.query.get(orderID)
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
    return jsonify({"msg":"Order cancelled successfully"}),200"""

#View all orders in admin dashboard
@orders.route("/admin/orders", methods=["GET"])
@jwt_required()
def view_orders():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.is_staff:
        return jsonify({"msg": "Unauthorized Access"}), 403
    
    order_records = Orders.query.filter(Orders.order_status != "Delivered")\
                         .order_by(Orders.order_date.desc()).all()
    order_list = []
    
    for order in order_records:
        
        order_list.append({
            "orderID": order.orderID,
            "user": f"{order.user.firstname} {order.user.lastname}",
            "email": order.user.email,
            "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "order_status": order.order_status,
            "total_amount": order.total_amount,
            
        })
        
    return jsonify({"orders":order_list}), 200  

#Click on action to view on a specific order in order details page
@orders.route("/admin/order/<int:orderID>", methods=["GET"])
@jwt_required()
def get_order_details(orderID):
    order = Orders.query.get(orderID)
    if not order:
        return jsonify({"msg":"Order not found"}),404
    items= []
    for item in order.items:
        items.append({
            "productName": item.product.productName,
            "quantity": item.quantity,
            "price": item.product.price,
            "sub_total": item.sub_total
        })


    data={
        "orderID": order.orderID,
        "user":{ 
            "name":f"{order.user.firstname} {order.user.lastname}",
            "email":order.user.email,
            "phone":order.user.phone,
        },
        "items": items,
        "total_amount": order.total_amount,
        "order_status": order.order_status,
        "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
    return jsonify(data), 200
    
#Update order status in order details page
@orders.route("/admin/order/update/<int:orderID>", methods=["PATCH"])
@jwt_required()
def update_order_status(orderID):
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.is_staff:
        return jsonify({"msg": "Unauthorized Access"}), 403
    
    order = Orders.query.get(orderID)
    
    if not order:
        return jsonify({"msg": "Order not found"}), 404
    
    data = request.get_json()
    new_status = data.get("order_status")
    
    if new_status not in ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]:
        return jsonify({"msg": "Invalid status"}), 400
    
    if new_status == "Cancelled" and order.order_status != "Cancelled":
        # Restock items in the order
        for item in order.items:
            product = Product.query.get(item.productID)
            if product:
                product.quantity += item.quantity
    
    order.order_status = new_status
    db.session.commit()
    
    return jsonify({"msg": f"Order status updated to {new_status}"}), 200
       