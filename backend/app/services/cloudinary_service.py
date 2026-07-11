import os
import cloudinary
import cloudinary.uploader
from app.core import config

# Check if Cloudinary credentials are set and configure the SDK
cloud_name = config.CLOUDINARY_CLOUD_NAME or os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = config.CLOUDINARY_API_KEY or os.getenv("CLOUDINARY_API_KEY")
api_secret = config.CLOUDINARY_API_SECRET or os.getenv("CLOUDINARY_API_SECRET")

if cloud_name and api_key and api_secret:
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )
else:
    print("Warning: Cloudinary credentials are not fully configured. Cloudinary uploads may fail.")

def upload_image_to_cloudinary(file_path_or_filelike) -> str:
    """
    Uploads an image to Cloudinary and returns the secure HTTPS URL.
    Can accept a local file path, file-like object, or bytes.
    """
    try:
        response = cloudinary.uploader.upload(
            file_path_or_filelike,
            folder="products"
        )
        secure_url = response.get("secure_url")
        if not secure_url:
            raise ValueError("Cloudinary upload did not return a secure URL.")
        return secure_url
    except Exception as e:
        print(f"Error uploading image to Cloudinary: {e}")
        raise e
