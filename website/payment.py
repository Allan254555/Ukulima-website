import requests, os, json, hmac, hashlib, datetime
from dotenv import load_dotenv
from datetime import datetime
import hashlib
from flask import Flask, request, jsonify, Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity

from .orders import create_order  # Ensure user authentication
from .models import db, Payment, Orders,OrderItem, Cart, User

load_dotenv() # Load environment variables from .env file
payment= Blueprint("payment", __name__) # Create a blueprint for payment routes

# Paystack API Keys from environment
PAYSTACK_SECRET_KEY = ""
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY")
PAYSTACK_API_URL = "https://api.paystack.co" # Paystack API URL


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
        "callback_url": "/paystack/callback", #
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

@payment.route("/paystack_webhook", methods=["POST"])
def paystack_webhook():
    data = request.get_json()

    if  data.get("event") != "charge.success":
        return jsonify({"message": "Invalid webhook event"}), 400

    payment_data = data["data"]
    reference = payment_data["reference"]
    status = payment_data["status"]

    if status != "success":
        return jsonify({"message": "Payment not successful"}), 400

    #find order by reference
    order = Orders.query.filter_by(paystack_reference=reference).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    
    #Check if the payment is already processed
    existing_payment = Payment.query.filter_by(transaction_reference=reference).first()
    if existing_payment and existing_payment.paymentStatus == "Success":
        return jsonify({"message": "Payment already processed"}), 200
    
    # Update the order status to "Processing"
    order.order_status = "Processing"
    db.session.commit()

    #update payment record
    if existing_payment:
        existing_payment.paymentStatus = "Success"
        db.session.commit()

    return jsonify({"message": "Payment verified and order updated"}), 200
