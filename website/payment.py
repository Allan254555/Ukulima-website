import requests, os, json, hmac, hashlib, datetime
from dotenv import load_dotenv
from datetime import datetime
import hashlib
from .cart import clear_cart
from flask import Flask, request, jsonify, Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from .orders import create_order,deduct_stock  # Ensure user authentication
from .models import db, Payment, Orders,OrderItem, Cart, User

load_dotenv() # Load environment variables from .env file
payment= Blueprint("payment", __name__) # Create a blueprint for payment routes

# Paystack API Keys from environment
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY")
PAYSTACK_API_URL = os.environ.get("PAYSTACK_API_URL") # Paystack API URL


# Initiate Paystack Payment
# This endpoint initiates a payment with Paystack for a specific order.
@payment.route('/paystack/initiate_payment/<int:orderID>', methods=['POST'])
@jwt_required()
def initiate_paystack_payment(orderID):
    """Fetch the order, generate and save a refference and then call paystack initialize"""
    data = request.get_json()
    phone = data.get("phone") # Get the phone number from the request data
    email = get_jwt_identity() # Get the email of the current user from JWT token
    user = User.query.filter_by(email=email).first() # Fetch the user from the database

    order = Orders.query.get(orderID)
    if not order or order.user_id != user.id:# Check if the order exists and belongs to the user
        return jsonify({"msg": "Invalid order"}), 404
    if order.order_status != "Unpaid":
        return jsonify({"msg": "Order already paid or processing"}), 400
    
    
    #Fetch phone number from request body if requested
    phone = user.phone
    if not phone:
        return jsonify({"msg": "Phone number is required"}), 400
    #Create a unique reference for the order and save it
    reference = f"FARM{orderID}{datetime.utcnow().strftime('%Y%m%d%H%M%S')}" 
    order.paystack_reference = reference
    db.session.commit()

    amount = int(order.total_amount * 100)  # Convert KES to smallest unit
    
    data = {
        "email": user.email,
        "amount": amount,
        "currency": "KES",
        "reference": reference,
        "callback_url": "http://localhost:5173/about", #
        "channels":["mobile_money"],
        "metadata":{
            "phone":phone,
            "custom_fields":[
                {
                    "display_name":"Phone Number",
                    "variable_name":"phone",
                    "value":phone
                }
            ]
        }
    }
     
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    #Initialize transaction with Paystack
    response = requests.post(f"{PAYSTACK_API_URL}/transaction/initialize", json=data, headers=headers)
    if response.status_code == 200:
        payment_url = response.json()['data']['authorization_url']
        reference = response.json()['data']['reference']
        
         # Create payment record with pending status
        payment = Payment(
            userID=user.id,
            orderID=order.orderID,
            paymentMethod="Paystack",
            amount=order.total_amount,
            currency="KES",
            paymentStatus="Pending",
            transaction_reference=reference,
            paymentDate=datetime.utcnow(),
        )
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({"url": payment_url}),200
    else:
        return jsonify({"msg": "Failed to initiate payment", "error": response.json()}), 400

@payment.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    data = request.get_json()

    
    if not data:
        return jsonify({"message":"No data received"}), 400 
      
    event = data.get("event")
    payment_data = data.get("data",{})
    reference = payment_data.get("reference")
    status = payment_data.get("status")
    
    if not reference:
        return jsonify({"message": "No reference found"}), 400


    #find order by reference
    order = Orders.query.filter_by(paystack_reference=reference).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    
    
    existing_payment = Payment.query.filter_by(transaction_reference=reference).first()
    
    #Handle successful payments
    if event == "charge.success" and status == "success":
        if existing_payment and existing_payment.paymentStatus == "Success":
            return jsonify({"message": "Payment already processed"}), 200
        
        
        deduction_result = deduct_stock(order.orderID, order.user_id)
        if not deduction_result["success"]:
            # If stock cannot be deducted, return a failed message with details of issues
            db.session.rollback()  # Rollback any changes made so far
            
            for item in deduction_result["items"]:
                cart_item= Cart.query.filter_by(productID=item["product_id"]).first()
                if cart_item:
                    cart_item.quantity = item["available"]
                    db.session.commit()
            return jsonify({
                "message": "Payment successful, but insufficient stock. Cart adjusted.",
                "insufficient_items": deduction_result["items"]
            }), 400                                                                                                                                                                                                                                                                                                                                                                                     
            
            # Update the payment record to success
        if existing_payment:
                existing_payment.paymentStatus = "Success"
            
        else:
                
                existing_payment = Payment(
                    userID=order.user_id,
                    orderID=order.orderID,
                    paymentMethod="Paystack",
                    amount=order.total_amount,
                    currency="KES",
                    paymentStatus="Success",
                    transaction_reference=reference,
                    paymentDate=datetime.utcnow(),
                )
        db.session.add(existing_payment)
        
        order.order_status = "Processing"
        db.session.commit()
            
        clear_cart(order.user_id)  # Clear the cart after successful payment
        
        return jsonify({"message": "Payment successful, order is now processing Cart cleared"}), 200

    # Handle failed payments 
    elif event in ["charge.failed", "charge.abandoned", "charge.expired"] or status != "success":
        if existing_payment:
            existing_payment.paymentStatus = "Failed"
            db.session.add(existing_payment)
        else:
            failed_payment = Payment(
                userID=order.user_id,
                orderID=order.orderID,
                paymentMethod="Paystack",
                amount=order.total_amount,
                currency="KES",
                paymentStatus="Failed",
                transaction_reference=reference,
                paymentDate=datetime.utcnow(),
            )
            db.session.add(failed_payment)

        order.order_status = "Cancelled"
        db.session.commit()
        return jsonify({"message": "Payment failed, Order Cancelled"}), 200

    return jsonify({"message": "Unhandled event"}), 400