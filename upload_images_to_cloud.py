import os
from website import create_app, db
from website.models import Product, Category
import cloudinary
import cloudinary.uploader

# Set up Flask app context
app = create_app()
app.app_context().push()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Path to static uploads folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "uploads")

# Upload categories
categories = Category.query.all()
for category in categories:
    local_path = os.path.join(UPLOAD_FOLDER, category.image_url)
    if os.path.exists(local_path):
        try:
            result = cloudinary.uploader.upload(local_path, folder="categories")
            category.image_url = result["secure_url"]
            print(f"Uploaded category: {category.name}")
        except Exception as e:
            print(f"Failed to upload {category.image_url}: {str(e)}")

# Upload products
products = Product.query.all()
for product in products:
    local_path = os.path.join(UPLOAD_FOLDER, product.image_url)
    if os.path.exists(local_path):
        try:
            result = cloudinary.uploader.upload(local_path, folder="products")
            product.image_url = result["secure_url"]
            print(f"Uploaded product: {product.productName}")
        except Exception as e:
            print(f"Failed to upload {product.image_url}: {str(e)}")

# Save updated URLs to the database
db.session.commit()
print("✅ Migration completed and URLs updated in the database.")


#delete images in uploads folder
import shutil

UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "uploads")
shutil.rmtree(UPLOAD_FOLDER)
print("🧹 Local uploads folder removed.")
