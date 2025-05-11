from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, User, Product, Category, Orders

admin_dashboard = Blueprint('admin_dashboard', __name__)

@admin_dashboard.route('/admin/summary', methods=['GET'])
@jwt_required()
def get_admin_summary():
   
    current_user_email = get_jwt_identity()
    admin_user = User.query.filter_by(email=current_user_email, role='admin').first()
    if not admin_user:
        return jsonify({"msg": "Unauthorized"}), 403

    total_users = User.query.count()
    total_products = Product.query.count()
    total_categories = Category.query.count()

    # Sum up total sales (only orders that are "Completed" or "Processing")
    total_sales = db.session.query(db.func.sum(Orders.total_amount))\
                             .filter(Orders.order_status.in_(["Completed", "Processing"]))\
                             .scalar() or 0

    return jsonify({
        "total_users": total_users,
        "total_products": total_products,
        "total_categories": total_categories,
        "total_sales": f"Ksh {total_sales:,.0f}"  
    }), 200
