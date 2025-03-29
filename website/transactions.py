import requests
import os
import json
import hmac
import hashlib
from flask import Flask, request, jsonify, Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user  # Ensure user authentication
from .models import db, Payment

views = Blueprint("views", __name__)

# Paystack API Keys
PAYSTACK_SECRET_KEY = "sk_test_055242fba8d7d8ffd40955ec127076bc8afad18a"
PAYSTACK_PUBLIC_KEY = "pk_test_333023a070f87dd363c25373f9b19e8e0300fd0e"


# Payment success & failure pages
@views.route('/payment_success')
def payment_success():
    return render_template('success.html')

@views.route('/payment_failure')
def payment_failure():
    return render_template('failure.html')

# Create Paystack Payment Session
@views.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        data = request.get_json().get("price_ids", [])
        print(data)  # Debugging

        # Calculate total price
        total_price = sum(int(item['price']) * int(item['quantity']) for item in data)
        if not PAYSTACK_SECRET_KEY:
            return jsonify({"error": "Payment secret key not set"}), 500
        # Prepare Paystack payload
        payload = {
            'email': current_user.email,  # User email
            'amount': total_price * 100,  # Convert to kobo
            'currency': 'KES',  # Use KES
            'callback_url': url_for('views.paystack_webhook', _external=True),
            'metadata': {"user_id": current_user.id}# Metadata for reference
        }

        # Create Paystack transaction
        headers = {'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}', 'Content-Type': 'application/json'}
        response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
        response_data = response.json()

        if response_data.get("status"):
            return redirect(response_data["data"]["authorization_url"])
        else:
            return jsonify({"error": "Payment Initialization Failed"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Paystack Webhook (Handles Payment Verification)
@views.route('/paystack-webhook', methods=['POST'])
def paystack_webhook():
    try:
        
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Paystack-Signature')

        # Compute expected signature
        computed_signature = hmac.new(
            PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        # Verify authenticity
        if computed_signature != signature:
            return jsonify({"error": "Invalid signature"}), 400

        event = json.loads(payload)

        if event.get("event") == "charge.success":
            transaction_data = event["data"]
            email = transaction_data["customer"]["email"]
            reference = transaction_data["reference"]

            # Find payment record and update status
            payment = Payment.query.filter_by(paystackReference=reference).first()
            if payment:
                payment.paymentStatus = "Completed"
                db.session.commit()
                return jsonify({"success": "Payment verified"}), 200
            else:
                return jsonify({"error": "Payment record not found"}), 404

        return jsonify({"message": "Event received"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
