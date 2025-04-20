from flask import Blueprint,render_template,jsonify,request,redirect,url_for,session
from.models import db,Cart,Product,User
from flask_jwt_extended import jwt_required,get_jwt_identity
from flask_login import login_required,current_user

cart =Blueprint("cart",__name__)

@cart.route('/cart_add', methods=['POST'])
@jwt_required()
def add_to_cart():
    try:
        data = request.get_json()
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()
        quantity = data.get('quantity', 1)  # Default to 1 if not provided
        productID = data.get('productID')
        
        #get product by productID
        product = Product.query.get(productID)
        if not product:
            return jsonify({"msg": "Product not found"}), 404

        if product.quantity < quantity:
            return jsonify({"msg": "Insufficient stock"}), 400

        #Check if product is already in cart
        cart_item = Cart.query.filter_by(user_id=user.id, productID=productID).first()
        if cart_item: #if product is already in cart update quantity
            if product.quantity >= quantity:
                cart_item.quantity += quantity
            else:
                return jsonify({"msg": "Insufficient stock"}), 400
        else:
            # Create new cart item
            total_price = quantity * product.price
            cart_item = Cart(user_id=user.id,
                             productID=productID,
                             quantity=quantity,
                             total_price=total_price 
                             )
            db.session.add(cart_item)

        db.session.commit()
        # Calculate total amount in cart
        cart_items = Cart.query.filter_by(user_id=user.id).all()
        total_amount = sum(item.total_price for item in cart_items)
        
        return jsonify({"msg": "Item added to cart",
                        "total_amount":total_amount}), 201       

    except Exception as e:
        db.session.rollback()  # Rollback transaction on failure
        return jsonify({"msg": "Error adding item to cart", "error": str(e)}), 500