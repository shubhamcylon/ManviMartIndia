import os
import re
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, or_, text
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "dev-secret-key"
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


# ======================
# Database Config
# ======================
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///manvimart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PREFERRED_URL_SCHEME'] = "https"


# ======================
# Email Config
# ======================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['STORE_EMAIL'] = os.environ.get("STORE_EMAIL") or 'manvimart@outlook.com'
app.config['ONLINE_PAYMENT_ENABLED'] = False
app.config['STORE_NAME'] = os.environ.get("STORE_NAME") or 'Manvi Mart India'
app.config['STORE_GSTIN'] = os.environ.get("STORE_GSTIN") or 'GSTIN_NOT_ADDED'
app.config['STORE_ADDRESS'] = os.environ.get("STORE_ADDRESS") or 'Haridwar, Uttarakhand, India'
app.config['STORE_STATE'] = os.environ.get("STORE_STATE") or 'Uttarakhand'
app.config['STORE_STATE_CODE'] = os.environ.get("STORE_STATE_CODE") or '05'
app.config['STORE_WHATSAPP_NUMBER'] = os.environ.get("STORE_WHATSAPP_NUMBER", "")
app.config['ORDER_ALERT_WHATSAPP_PHONE'] = os.environ.get("ORDER_ALERT_WHATSAPP_PHONE", "")
app.config['ORDER_ALERT_WHATSAPP_APIKEY'] = os.environ.get("ORDER_ALERT_WHATSAPP_APIKEY", "")
app.config['GOOGLE_SHEET_WEBHOOK_URL'] = os.environ.get("GOOGLE_SHEET_WEBHOOK_URL", "")
app.config['GOOGLE_SHEET_WEBHOOK_TOKEN'] = os.environ.get("GOOGLE_SHEET_WEBHOOK_TOKEN", "")


db = SQLAlchemy(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)


# ======================
# Products
# ======================
products = [
    {
        "id": 1,
        "name": "Draw Graphic T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Cotton graphic t-shirt with a clean regular fit and soft hand feel.",
        "image": "assets/img/products/men-draw-black-tshirt.jpg",
        "gallery": [
            "assets/img/products/men-draw-black-tshirt.jpg",
            "assets/img/products/men-draw-black-tshirt-front-alt.jpg",
            "assets/img/products/men-draw-black-tshirt-back.jpg",
            "assets/img/products/men-draw-black-tshirt-detail.jpg",
        ],
    },
    {
        "id": 2,
        "name": "Confused Black T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Black statement graphic t-shirt designed for everyday street styling.",
        "image": "assets/img/products/men-confused-black-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-confused-black-tshirt-front.jpg",
            "assets/img/products/men-confused-black-tshirt-side.jpg",
            "assets/img/products/men-confused-black-tshirt-back.jpg",
            "assets/img/products/men-confused-black-tshirt-detail.jpg",
        ],
    },
    {
        "id": 3,
        "name": "Burgundy Floral Top",
        "price": 399,
        "hsn": "6206",
        "gst_rate": 5,
        "category": "female-top",
        "description": "Flowy floral top in deep burgundy with embroidered neckline details.",
        "image": "assets/img/products/women-burgundy-floral-top-front.jpg",
        "gallery": [
            "assets/img/products/women-burgundy-floral-top-front.jpg",
            "assets/img/products/women-burgundy-floral-top-side.jpg",
            "assets/img/products/women-burgundy-floral-top-back.jpg",
            "assets/img/products/women-burgundy-floral-top-detail.jpg",
        ],
    },
    {
        "id": 4,
        "name": "Orange Floral Top",
        "price": 399,
        "hsn": "6206",
        "gst_rate": 5,
        "category": "female-top",
        "description": "Bright orange printed top with lightweight drape and relaxed shape.",
        "image": "assets/img/products/women-orange-floral-top-front.jpg",
        "gallery": [
            "assets/img/products/women-orange-floral-top-front.jpg",
            "assets/img/products/women-orange-floral-top-side.jpg",
            "assets/img/products/women-orange-floral-top-back.jpg",
            "assets/img/products/women-orange-floral-top-detail.jpg",
        ],
    },
    {
        "id": 5,
        "name": "Pink Floral Top",
        "price": 399,
        "hsn": "6206",
        "gst_rate": 5,
        "category": "female-top",
        "description": "Soft pink floral top with airy sleeves and a statement silhouette.",
        "image": "assets/img/products/women-pink-floral-top-front.jpg",
        "gallery": [
            "assets/img/products/women-pink-floral-top-front.jpg",
            "assets/img/products/women-pink-floral-top-side.jpg",
            "assets/img/products/women-pink-floral-top-back.jpg",
            "assets/img/products/women-pink-floral-top-detail.jpg",
        ],
    },
    {
        "id": 6,
        "name": "Breeze Beige T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Neutral beige t-shirt with clean graphic placement and modern fit.",
        "image": "assets/img/products/men-breeze-beige-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-breeze-beige-tshirt-front.jpg",
            "assets/img/products/men-breeze-beige-tshirt-side.jpg",
            "assets/img/products/men-breeze-beige-tshirt-back.jpg",
            "assets/img/products/men-breeze-beige-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 7,
        "name": "Future Yellow T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Bright yellow crew neck tee with FUTURE chest graphic for daily wear.",
        "image": "assets/img/products/men-future-yellow-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-future-yellow-tshirt-front.jpg",
            "assets/img/products/men-future-yellow-tshirt-front-alt.jpg",
            "assets/img/products/men-future-yellow-tshirt-back.jpg",
            "assets/img/products/men-future-yellow-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 8,
        "name": "Strong Yellow T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Athletic yellow t-shirt featuring a bold BE STRONG slogan print.",
        "image": "assets/img/products/men-strong-yellow-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-strong-yellow-tshirt-front.jpg",
            "assets/img/products/men-strong-yellow-tshirt-side.jpg",
            "assets/img/products/men-strong-yellow-tshirt-back.jpg",
            "assets/img/products/men-strong-yellow-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 9,
        "name": "Think Coral T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Coral streetwear tee with THINK typography and relaxed fit shape.",
        "image": "assets/img/products/men-think-coral-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-think-coral-tshirt-front.jpg",
            "assets/img/products/men-think-coral-tshirt-front-alt.jpg",
            "assets/img/products/men-think-coral-tshirt-back.jpg",
            "assets/img/products/men-think-coral-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 10,
        "name": "Vibes Blue T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Blue graphic t-shirt with VIBES chest artwork and a soft finish.",
        "image": "assets/img/products/men-vibes-blue-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-vibes-blue-tshirt-front.jpg",
            "assets/img/products/men-vibes-blue-tshirt-side.jpg",
            "assets/img/products/men-vibes-blue-tshirt-back.jpg",
            "assets/img/products/men-vibes-blue-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 11,
        "name": "Vibes Grey T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Cool grey graphic tee with minimal contrast print and clean silhouette.",
        "image": "assets/img/products/men-vibes-grey-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-vibes-grey-tshirt-front.jpg",
            "assets/img/products/men-vibes-grey-tshirt-front-alt.jpg",
            "assets/img/products/men-vibes-grey-tshirt-back.jpg",
            "assets/img/products/men-vibes-grey-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 12,
        "name": "Expand Green T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Muted green tee with EXPAND print and everyday regular fit profile.",
        "image": "assets/img/products/men-expand-green-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-expand-green-tshirt-front.jpg",
            "assets/img/products/men-expand-green-tshirt-front-alt.jpg",
            "assets/img/products/men-expand-green-tshirt-back.jpg",
            "assets/img/products/men-green-graphic-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 13,
        "name": "Destiny Green T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Deep green crew neck t-shirt with BRING DESTINY centered typography.",
        "image": "assets/img/products/men-destiny-green-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-destiny-green-tshirt-front.jpg",
            "assets/img/products/men-destiny-green-tshirt-side.jpg",
            "assets/img/products/men-destiny-green-tshirt-back.jpg",
            "assets/img/products/men-destiny-green-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 14,
        "name": "Embrace Black T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Classic black t-shirt with EMBRACE statement block artwork.",
        "image": "assets/img/products/men-embrace-black-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-embrace-black-tshirt-front.jpg",
            "assets/img/products/men-embrace-black-tshirt-side.jpg",
            "assets/img/products/men-embrace-black-tshirt-back.jpg",
            "assets/img/products/men-embrace-black-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 15,
        "name": "Adventure Coral T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Coral crew neck tee with ADVENTURE chest print and clean drape.",
        "image": "assets/img/products/men-adventure-coral-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-adventure-coral-tshirt-front.jpg",
            "assets/img/products/men-adventure-coral-tshirt-side.jpg",
            "assets/img/products/men-adventure-coral-tshirt-back.jpg",
            "assets/img/products/men-adventure-coral-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 16,
        "name": "White Floral lower",
        "price": 399,
        "hsn": "6204",
        "gst_rate": 5,
        "category": "coord-set",
        "description": "Flowy white floral co-ord with wide-leg fit for summer styling.",
        "image": "assets/img/products/women-white-floral-coord-set-front.jpg",
        "gallery": [
            "assets/img/products/women-white-floral-coord-set-front.jpg",
            "assets/img/products/women-white-floral-coord-set-side.jpg",
            "assets/img/products/women-white-floral-coord-set-back.jpg",
            "assets/img/products/women-white-floral-coord-set-detail-pattern.jpg",
            "assets/img/products/women-white-floral-coord-set-detail-waistband.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 17,
        "name": "Aqua Floral Lower",
        "price": 399,
        "hsn": "6204",
        "gst_rate": 5,
        "category": "coord-set",
        "description": "Aqua floral co-ord with airy shape and statement botanical print.",
        "image": "assets/img/products/women-aqua-floral-coord-set-front.jpg",
        "gallery": [
            "assets/img/products/women-aqua-floral-coord-set-front.jpg",
            "assets/img/products/women-aqua-floral-coord-set-side.jpg",
            "assets/img/products/women-aqua-floral-coord-set-back.jpg",
            "assets/img/products/women-aqua-floral-coord-set-detail-pattern.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 18,
        "name": "Navy Floral Lower",
        "price": 399,
        "hsn": "6204",
        "gst_rate": 5,
        "category": "coord-set",
        "description": "Navy floral co-ord set designed with a relaxed and fluid silhouette.",
        "image": "assets/img/products/women-navy-floral-coord-set-front.jpg",
        "gallery": [
            "assets/img/products/women-navy-floral-coord-set-front.jpg",
            "assets/img/products/women-navy-floral-coord-set-side.jpg",
            "assets/img/products/women-navy-floral-coord-set-back.jpg",
            "assets/img/products/women-navy-floral-coord-set-detail-pattern.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 19,
        "name": "Magenta Leaf Top",
        "price": 299,
        "hsn": "6206",
        "gst_rate": 5,
        "category": "female-top",
        "description": "Magenta printed top with soft texture and gathered yoke detailing.",
        "image": "assets/img/products/women-magenta-leaf-top-front.jpg",
        "gallery": [
            "assets/img/products/women-magenta-leaf-top-front.jpg",
            "assets/img/products/women-magenta-leaf-top-side.jpg",
            "assets/img/products/women-magenta-leaf-top-back.jpg",
            "assets/img/products/women-magenta-leaf-top-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 20,
        "name": "Olive Leaf Top",
        "price": 299,
        "hsn": "6206",
        "gst_rate": 5,
        "category": "female-top",
        "description": "Olive leaf-print top with flowy sleeves and a flattering fall.",
        "image": "assets/img/products/women-olive-leaf-top-front.jpg",
        "gallery": [
            "assets/img/products/women-olive-leaf-top-front.jpg",
            "assets/img/products/women-olive-leaf-top-side.jpg",
            "assets/img/products/women-olive-leaf-top-back.jpg",
            "assets/img/products/women-olive-leaf-top-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 21,
        "name": "Teal Leaf Top",
        "price": 299,
        "hsn": "6206",
        "gst_rate": 5,
        "category": "female-top",
        "description": "Teal leaf top with contrast placket texture and lightweight comfort.",
        "image": "assets/img/products/women-teal-leaf-top-front.jpg",
        "gallery": [
            "assets/img/products/women-teal-leaf-top-front.jpg",
            "assets/img/products/women-teal-leaf-top-side.jpg",
            "assets/img/products/women-teal-leaf-top-back.jpg",
            "assets/img/products/women-teal-leaf-top-detail.jpg",
        ],
        "is_new_arrival": True,
    },
    {
        "id": 22,
        "name": "Gysber Blue T-shirt",
        "price": 299,
        "hsn": "6109",
        "gst_rate": 5,
        "category": "tshirt",
        "description": "Blue GRYSBER print t-shirt with comfortable fit and daily styling.",
        "image": "assets/img/products/men-gysber-blue-tshirt-front.jpg",
        "gallery": [
            "assets/img/products/men-gysber-blue-tshirt-front.jpg",
            "assets/img/products/men-gysber-blue-tshirt-front-alt.jpg",
            "assets/img/products/men-gysber-blue-tshirt-back.jpg",
            "assets/img/products/men-gysber-blue-tshirt-detail.jpg",
        ],
        "is_new_arrival": True,
    },
]

# Category-first pricing requested for current collection.
CATEGORY_BASE_PRICES = {
    "tshirt": 299,
    "oversize-tshirt": 499,
    "coord-set": 499,
    "female-top": 399,
}

for product in products:
    category = product.get("category")
    if category in CATEGORY_BASE_PRICES:
        product["price"] = CATEGORY_BASE_PRICES[category]
    product.setdefault("country_of_origin", "India")
    product.setdefault("net_quantity", "1 N")

INDIAN_STATES = {
    "Andaman and Nicobar Islands": "35",
    "Andhra Pradesh": "37",
    "Arunachal Pradesh": "12",
    "Assam": "18",
    "Bihar": "10",
    "Chandigarh": "04",
    "Chhattisgarh": "22",
    "Dadra and Nagar Haveli and Daman and Diu": "26",
    "Delhi": "07",
    "Goa": "30",
    "Gujarat": "24",
    "Haryana": "06",
    "Himachal Pradesh": "02",
    "Jammu and Kashmir": "01",
    "Jharkhand": "20",
    "Karnataka": "29",
    "Kerala": "32",
    "Ladakh": "38",
    "Lakshadweep": "31",
    "Madhya Pradesh": "23",
    "Maharashtra": "27",
    "Manipur": "14",
    "Meghalaya": "17",
    "Mizoram": "15",
    "Nagaland": "13",
    "Odisha": "21",
    "Puducherry": "34",
    "Punjab": "03",
    "Rajasthan": "08",
    "Sikkim": "11",
    "Tamil Nadu": "33",
    "Telangana": "36",
    "Tripura": "16",
    "Uttar Pradesh": "09",
    "Uttarakhand": "05",
    "West Bengal": "19",
}

PAYMENT_METHODS = {
    "cod": "Cash on Delivery",
    "upi": "UPI after confirmation",
    "bank_transfer": "Bank Transfer after confirmation",
}

categories = {
    "tshirt": "T-shirt",
    "oversize-tshirt": "Oversize T-shirt",
    "coord-set": "Co-ord Set",
    "female-top": "Floral Top",
    "men": "Men Fashion",
    "men-tshirt": "Men T-shirt",
    "men-oversize-tshirt": "Men Oversize T-shirt",
    "men-new-arrival": "Men New Arrival",
    "women": "Women Fashion",
    "women-coord-set": "Women Co-ord Set",
    "women-top": "Women Floral Top",
    "women-new-arrival": "Women New Arrival",
    "new-arrivals": "New Arrivals",
}

marketplaces = {
    "flipkart": "Flipkart",
    "amazon": "Amazon",
    "meesho": "Meesho",
}

blog_posts = [
    {
        "slug": "best-tshirt-lower-combinations-men",
        "title": "Best T-shirt and Lower Combinations for Men",
        "excerpt": "Simple styling ideas for pairing men's t-shirts, lowers and trousers for daily wear.",
        "category": "Men Fashion",
        "date": "May 9, 2026",
        "image": "assets/img/products/men-think-coral-tshirt-front.jpg",
        "keywords": ["men t-shirt", "men lower", "men trouser"],
        "content": [
            "A solid t-shirt with a comfortable lower works well for relaxed daily wear. For a sharper look, pair a clean t-shirt with a smart trouser.",
            "When choosing men's clothing online, compare fabric, fit, size chart and seller ratings before buying."
        ],
    },
    {
        "slug": "kurti-kurta-suit-shopping-guide",
        "title": "Kurti, Kurta and Suit Shopping Guide for Women",
        "excerpt": "A quick guide to choosing kurtis, kurtas and suit sets by fabric, fit and occasion.",
        "category": "Women Fashion",
        "date": "May 9, 2026",
        "image": "assets/img/products/women-magenta-leaf-top-front.jpg",
        "keywords": ["kurti", "kurta", "women suit"],
        "content": [
            "Kurtis and kurtas are easy everyday picks, while suit sets work well for functions, office wear and festive occasions.",
            "Check fabric, size chart, sleeve length and return policy before placing your order on any marketplace."
        ],
    },
    {
        "slug": "kids-clothes-online-buying-guide",
        "title": "Kids Clothes Online Buying Guide",
        "excerpt": "How to choose comfortable kids t-shirts, lowers and everyday clothing online.",
        "category": "Kids Fashion",
        "date": "May 9, 2026",
        "image": "assets/img/products/kids-clothes-buying-guide.jpg",
        "keywords": ["kids clothes", "kids t-shirt", "kids lower"],
        "content": [
            "Kids clothing should be soft, breathable and easy to wash. Always choose comfort before heavy design.",
            "Compare age size, height fit, fabric and return policy before buying kids clothes online."
        ],
    },
]

def get_product(pid):
    return next((p for p in products if p["id"] == pid), None)


def get_blog_post(slug):
    return next((post for post in blog_posts if post["slug"] == slug), None)


def marketplace_url(product, marketplace):
    links = product.get("marketplace_urls", {})
    if links.get(marketplace):
        return links[marketplace]
    if product.get("id"):
        return url_for("product_detail", pid=product["id"])
    return url_for("products_page")


def product_matches_category(product, slug):
    product_category = product.get("category")
    is_new_arrival = product.get("is_new_arrival", False)
    if product_category == slug:
        return True
    if slug == "men":
        return product_category in {"tshirt", "oversize-tshirt"}
    if slug == "women":
        return product_category in {"coord-set", "female-top"}
    if slug == "tshirt":
        return product_category == "tshirt"
    if slug in {"men-tshirt", "men-oversize-tshirt"}:
        return product_category in {"tshirt", "oversize-tshirt"}
    if slug == "women-coord-set":
        return product_category == "coord-set"
    if slug == "women-top":
        return product_category == "female-top"
    if slug == "new-arrivals":
        return is_new_arrival
    if slug == "men-new-arrival":
        return product_category in {"tshirt", "oversize-tshirt"} and is_new_arrival
    if slug == "women-new-arrival":
        return product_category in {"coord-set", "female-top"} and is_new_arrival
    return False


def get_products_for_category(slug):
    return [product for product in products if product_matches_category(product, slug)]


def normalize_phone(phone):
    return re.sub(r"\D", "", phone or "")


def is_valid_phone(phone):
    return bool(re.fullmatch(r"\d{10,15}", normalize_phone(phone)))


def is_valid_password(password):
    return len(password or "") >= 8


def get_user_addresses(user_id):
    return UserAddress.query.filter_by(user_id=user_id).order_by(
        UserAddress.is_default.desc(),
        UserAddress.created_at.desc()
    ).all()


def validate_shipping_details(shipping_address, shipping_city, shipping_state, shipping_pincode, shipping_country):
    if not shipping_address or not shipping_city or not shipping_state or not shipping_pincode:
        return "Please fill all delivery address details."
    if shipping_state not in INDIAN_STATES:
        return "Please select a valid Indian state."
    if not re.fullmatch(r"\d{6}", shipping_pincode):
        return "Please enter a valid 6 digit Indian pincode."
    if (shipping_country or "").strip().lower() != "india":
        return "Orders are available only within India."
    return None


def safe_next_url(default_endpoint="home"):
    next_url = request.args.get("next") or request.form.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return url_for(default_endpoint)


def require_login():
    if "user_id" not in session:
        flash("Please sign in or create an account to continue.", "warning")
        next_url = request.path
        if request.method == "POST":
            next_url = request.referrer or url_for("products_page")
        return redirect(url_for("login", next=next_url))
    return None


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_gst_inclusive(gross_amount, gst_rate):
    gross_amount = money(gross_amount)
    gst_rate = Decimal(str(gst_rate))
    taxable = money(gross_amount * Decimal("100") / (Decimal("100") + gst_rate))
    gst_amount = money(gross_amount - taxable)
    return taxable, gst_amount


def build_cart_totals(cart, shipping_state=None):
    is_intra_state = shipping_state == app.config['STORE_STATE']
    subtotal = Decimal("0.00")
    taxable_total = Decimal("0.00")
    cgst_total = Decimal("0.00")
    sgst_total = Decimal("0.00")
    igst_total = Decimal("0.00")
    rows = []

    for pid, item in cart.items():
        product = get_product(int(pid))
        gst_rate = Decimal(str(item.get("gst_rate", product.get("gst_rate", 18) if product else 18)))
        hsn = item.get("hsn", product.get("hsn", "") if product else "")
        price = money(item["price"])
        quantity = int(item["qty"])
        line_total = money(price * quantity)
        taxable, gst_amount = calculate_gst_inclusive(line_total, gst_rate)

        if is_intra_state:
            cgst = money(gst_amount / 2)
            sgst = money(gst_amount - cgst)
            igst = Decimal("0.00")
        else:
            cgst = Decimal("0.00")
            sgst = Decimal("0.00")
            igst = gst_amount

        rows.append({
            "pid": int(pid),
            "name": item["name"],
            "price": price,
            "quantity": quantity,
            "hsn": hsn,
            "gst_rate": gst_rate,
            "line_total": line_total,
            "taxable": taxable,
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
        })
        subtotal += line_total
        taxable_total += taxable
        cgst_total += cgst
        sgst_total += sgst
        igst_total += igst

    gst_total = money(cgst_total + sgst_total + igst_total)
    return {
        "rows": rows,
        "subtotal": money(subtotal),
        "taxable_total": money(taxable_total),
        "cgst_total": money(cgst_total),
        "sgst_total": money(sgst_total),
        "igst_total": money(igst_total),
        "gst_total": gst_total,
        "grand_total": money(subtotal),
        "is_intra_state": is_intra_state,
    }


def format_inr(value):
    return f"{money(value):.2f}"


def normalize_whatsapp_number(phone):
    digits = normalize_phone(phone)
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 10:
        digits = f"91{digits}"
    return digits


def build_order_alert_text(order):
    lines = [
        "New order placed on Manvi Mart",
        f"Tracking ID: {order.tracking_id}",
        f"Invoice: {order.invoice_no}",
        f"Customer: {order.customer_name}",
        f"Phone: {order.customer_phone}",
        f"Email: {order.customer_email}",
        f"Payment: {PAYMENT_METHODS.get(order.payment_method, order.payment_method)}",
        "Items:",
    ]

    for item in order.items:
        lines.append(
            f"- {item.product_name} x {item.quantity} = Rs. {format_inr(item.line_total)}"
        )

    lines.extend([
        f"Total: Rs. {format_inr(order.total_amount)}",
        (
            "Address: "
            f"{order.shipping_address}, {order.shipping_city}, {order.shipping_state} - "
            f"{order.shipping_pincode}, {order.shipping_country}"
        ),
    ])
    return "\n".join(lines)


def build_google_sheet_order_payload(order):
    return {
        "tracking_id": order.tracking_id,
        "invoice_no": order.invoice_no,
        "created_at": order.created_at.isoformat() if order.created_at else "",
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "customer_phone": order.customer_phone,
        "payment_method": PAYMENT_METHODS.get(order.payment_method, order.payment_method),
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "shipping_address": order.shipping_address,
        "shipping_city": order.shipping_city,
        "shipping_state": order.shipping_state,
        "shipping_pincode": order.shipping_pincode,
        "shipping_country": order.shipping_country,
        "subtotal": format_inr(order.subtotal_amount),
        "taxable_amount": format_inr(order.taxable_amount),
        "cgst": format_inr(order.cgst_amount),
        "sgst": format_inr(order.sgst_amount),
        "igst": format_inr(order.igst_amount),
        "gst_total": format_inr(order.gst_amount),
        "grand_total": format_inr(order.total_amount),
        "items": [
            {
                "product_id": item.product_id,
                "name": item.product_name,
                "hsn": item.hsn_code,
                "gst_rate": format_inr(item.gst_rate),
                "quantity": item.quantity,
                "price": format_inr(item.price),
                "line_total": format_inr(item.line_total),
            }
            for item in order.items
        ],
    }


def send_google_sheet_order_alert(order):
    webhook_url = app.config.get("GOOGLE_SHEET_WEBHOOK_URL", "").strip()
    webhook_token = app.config.get("GOOGLE_SHEET_WEBHOOK_TOKEN", "").strip()
    if not webhook_url:
        return False

    if webhook_token:
        separator = "&" if "?" in webhook_url else "?"
        webhook_url = f"{webhook_url}{separator}{urlencode({'token': webhook_token})}"

    payload = json.dumps(build_google_sheet_order_payload(order)).encode("utf-8")
    request_obj = Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urlopen(request_obj, timeout=10) as response:
            return 200 <= getattr(response, "status", 200) < 300
    except (HTTPError, URLError):
        app.logger.exception("Google Sheet webhook failed for order %s", order.tracking_id)
    except Exception:
        app.logger.exception("Unexpected Google Sheet webhook error for %s", order.tracking_id)
    return False


def send_store_order_email(order, alert_text):
    store_email = app.config.get("STORE_EMAIL")
    mail_username = app.config.get("MAIL_USERNAME")
    mail_password = app.config.get("MAIL_PASSWORD")
    if not store_email or not mail_username or not mail_password:
        return False

    try:
        msg = Message(
            subject=f"New Order {order.tracking_id} | Rs. {format_inr(order.total_amount)}",
            sender=mail_username,
            recipients=[store_email],
            body=alert_text,
        )
        mail.send(msg)
        return True
    except Exception:
        app.logger.exception("Order email notification failed for %s", order.tracking_id)
        return False


def send_whatsapp_order_alert(alert_text):
    phone = normalize_whatsapp_number(app.config.get("ORDER_ALERT_WHATSAPP_PHONE", ""))
    api_key = app.config.get("ORDER_ALERT_WHATSAPP_APIKEY")
    if not phone or not api_key:
        return False

    query = urlencode({
        "phone": phone,
        "text": alert_text,
        "apikey": api_key,
    })
    endpoint = f"https://api.callmebot.com/whatsapp.php?{query}"

    try:
        with urlopen(endpoint, timeout=10) as response:
            return 200 <= getattr(response, "status", 200) < 300
    except (HTTPError, URLError):
        app.logger.exception("WhatsApp order notification failed.")
    except Exception:
        app.logger.exception("Unexpected WhatsApp notification error.")
    return False


def send_order_alerts(order):
    alert_text = build_order_alert_text(order)
    results = {
        "email": send_store_order_email(order, alert_text),
        "whatsapp": send_whatsapp_order_alert(alert_text),
    }
    if not any(results.values()):
        app.logger.warning(
            "Order %s placed but no notification channel is configured.",
            order.tracking_id
        )
    return results


# ======================
# User Model
# ======================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(200), nullable=False)
    orders = db.relationship("Order", backref="user", lazy=True)
    wishlist_items = db.relationship("WishlistItem", backref="user", lazy=True, cascade="all, delete-orphan")
    addresses = db.relationship("UserAddress", backref="user", lazy=True, cascade="all, delete-orphan")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(40), unique=True, nullable=False)
    tracking_id = db.Column(db.String(40), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False, default="")
    shipping_state = db.Column(db.String(80), nullable=False, default="")
    shipping_state_code = db.Column(db.String(5), nullable=False, default="")
    shipping_pincode = db.Column(db.String(10), nullable=False, default="")
    shipping_country = db.Column(db.String(80), nullable=False, default="India")
    payment_method = db.Column(db.String(50), nullable=False, default="cod")
    subtotal_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    taxable_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    cgst_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    sgst_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    igst_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    gst_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.String(30), nullable=False, default="Pending")
    order_status = db.Column(db.String(30), nullable=False, default="Order Enquiry")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer)
    product_name = db.Column(db.String(150), nullable=False)
    hsn_code = db.Column(db.String(20), nullable=False, default="")
    gst_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    taxable_value = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    cgst_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    sgst_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    igst_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)


class WishlistItem(db.Model):
    __tablename__ = "wishlist_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class UserAddress(db.Model):
    __tablename__ = "user_addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    label = db.Column(db.String(50), nullable=False, default="Home")
    recipient_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(80), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    country = db.Column(db.String(80), nullable=False, default="India")
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# ======================
# Create / Update Database
# ======================
def ensure_schema():
    db.create_all()
    inspector = inspect(db.engine)
    user_columns = {column["name"] for column in inspector.get_columns("user")}
    if "phone" not in user_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN phone VARCHAR(20)"))
        db.session.commit()

    order_columns = {column["name"] for column in inspector.get_columns("orders")}
    if "shipping_country" not in order_columns:
        db.session.execute(text("ALTER TABLE orders ADD COLUMN shipping_country VARCHAR(80) NOT NULL DEFAULT 'India'"))
        db.session.commit()
        order_columns.add("shipping_country")

    order_column_sql = {
        "tracking_id": "ALTER TABLE orders ADD COLUMN tracking_id VARCHAR(40)",
        "shipping_city": "ALTER TABLE orders ADD COLUMN shipping_city VARCHAR(100) NOT NULL DEFAULT ''",
        "shipping_state": "ALTER TABLE orders ADD COLUMN shipping_state VARCHAR(80) NOT NULL DEFAULT ''",
        "shipping_state_code": "ALTER TABLE orders ADD COLUMN shipping_state_code VARCHAR(5) NOT NULL DEFAULT ''",
        "shipping_pincode": "ALTER TABLE orders ADD COLUMN shipping_pincode VARCHAR(10) NOT NULL DEFAULT ''",
        "payment_method": "ALTER TABLE orders ADD COLUMN payment_method VARCHAR(50) NOT NULL DEFAULT 'cod'",
        "subtotal_amount": "ALTER TABLE orders ADD COLUMN subtotal_amount NUMERIC(10, 2) NOT NULL DEFAULT 0",
        "taxable_amount": "ALTER TABLE orders ADD COLUMN taxable_amount NUMERIC(10, 2) NOT NULL DEFAULT 0",
        "cgst_amount": "ALTER TABLE orders ADD COLUMN cgst_amount NUMERIC(10, 2) NOT NULL DEFAULT 0",
        "sgst_amount": "ALTER TABLE orders ADD COLUMN sgst_amount NUMERIC(10, 2) NOT NULL DEFAULT 0",
        "igst_amount": "ALTER TABLE orders ADD COLUMN igst_amount NUMERIC(10, 2) NOT NULL DEFAULT 0",
        "gst_amount": "ALTER TABLE orders ADD COLUMN gst_amount NUMERIC(10, 2) NOT NULL DEFAULT 0",
    }
    for column_name, sql in order_column_sql.items():
        if column_name not in order_columns:
            db.session.execute(text(sql))
            db.session.commit()

    if "tracking_id" not in order_columns:
        orders = Order.query.all()
        for order in orders:
            order.tracking_id = f"MMT-{order.id:06d}"
        db.session.commit()

    item_columns = {column["name"] for column in inspector.get_columns("order_items")}
    item_column_sql = {
        "hsn_code": "ALTER TABLE order_items ADD COLUMN hsn_code VARCHAR(20) NOT NULL DEFAULT ''",
        "gst_rate": "ALTER TABLE order_items ADD COLUMN gst_rate NUMERIC(5, 2) NOT NULL DEFAULT 0",
        "taxable_value": "ALTER TABLE order_items ADD COLUMN taxable_value NUMERIC(10, 2) NOT NULL DEFAULT 0",
        "cgst_amount": "ALTER TABLE order_items ADD COLUMN cgst_amount NUMERIC(10, 2) NOT NULL DEFAULT 0",
        "sgst_amount": "ALTER TABLE order_items ADD COLUMN sgst_amount NUMERIC(10, 2) NOT NULL DEFAULT 0",
        "igst_amount": "ALTER TABLE order_items ADD COLUMN igst_amount NUMERIC(10, 2) NOT NULL DEFAULT 0",
    }
    for column_name, sql in item_column_sql.items():
        if column_name not in item_columns:
            db.session.execute(text(sql))
            db.session.commit()


with app.app_context():
    ensure_schema()

# ======================
# Context Processors
# ======================
@app.context_processor
def inject_user():
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
        return dict(current_user=user)
    return dict(current_user=None)


@app.context_processor
def inject_wishlist():
    if "user_id" not in session:
        return dict(wishlist_product_ids=set())
    product_ids = {
        item.product_id
        for item in WishlistItem.query.filter_by(user_id=session["user_id"]).all()
    }
    return dict(wishlist_product_ids=product_ids)


@app.context_processor
def cart_counter():
    cart = session.get("cart", {})
    count = sum(item["qty"] for item in cart.values())
    return dict(cart_count=count)


@app.context_processor
def store_settings():
    return dict(
        store_email=app.config['STORE_EMAIL'],
        store_whatsapp_number=app.config['STORE_WHATSAPP_NUMBER'],
        online_payment_enabled=app.config['ONLINE_PAYMENT_ENABLED'],
        store_name=app.config['STORE_NAME'],
        store_gstin=app.config['STORE_GSTIN'],
        store_address=app.config['STORE_ADDRESS'],
        store_state=app.config['STORE_STATE'],
        store_state_code=app.config['STORE_STATE_CODE'],
        marketplace_url=marketplace_url,
        marketplaces=marketplaces,
        categories=categories,
        blog_posts=blog_posts,
        current_year=datetime.utcnow().year
    )


# ======================
# Home
# ======================
@app.route("/")
def home():
    return render_template(
        "index.html",
        products=products
    )


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


@app.route("/robots.txt")
def robots_txt():
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {url_for('sitemap_xml', _external=True)}",
    ])
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    urls = [
        url_for("home", _external=True),
        url_for("products_page", _external=True),
        url_for("blogs_page", _external=True),
        url_for("about", _external=True),
        url_for("contact", _external=True),
        url_for("privacy_policy", _external=True),
        url_for("return_policy", _external=True),
        url_for("terms_and_condition", _external=True),
    ]
    urls.extend(url_for("product_detail", pid=product["id"], _external=True) for product in products)
    urls.extend(url_for("category_page", slug=slug, _external=True) for slug in categories)
    urls.extend(url_for("blog_detail", slug=post["slug"], _external=True) for post in blog_posts)
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    body.extend(f"<url><loc>{url}</loc></url>" for url in urls)
    body.append("</urlset>")
    return Response("\n".join(body), mimetype="application/xml")


# ======================
# Products Page
# ======================
@app.route("/product")
def products_page():
    query = request.args.get("q")
    if query:
        filtered = [p for p in products if query.lower() in p["name"].lower()]
    else:
        filtered = products
    return render_template(
        "product.html",
        products=filtered
    )


@app.route("/product/<int:pid>")
def product_detail(pid):
    product = get_product(pid)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("products_page"))

    related_products = [
        p for p in products
        if p["id"] != product["id"] and p.get("category") == product.get("category")
    ][:4]

    return render_template(
        "product_detail.html",
        product=product,
        related_products=related_products
    )


@app.route("/category/<slug>")
def category_page(slug):
    if slug not in categories:
        flash("This category is not available. Please explore our clothing collection.", "info")
        return redirect(url_for("products_page"))
    category_name = categories[slug]
    category_products = get_products_for_category(slug)
    if category_products:
        return render_template(
            "category_products.html",
            category_name=category_name,
            products=category_products
        )
    return render_template(
        "category_coming_soon.html",
        category_name=category_name
    )


@app.route("/marketplace/<slug>")
def marketplace_page(slug):
    marketplace_name = marketplaces.get(slug, "Marketplace")
    return render_template(
        "marketplace_coming_soon.html",
        marketplace_name=marketplace_name
    )


@app.route("/blogs")
def blogs_page():
    return render_template("blogs.html", posts=blog_posts)


@app.route("/blog/<slug>")
def blog_detail(slug):
    post = get_blog_post(slug)
    if not post:
        flash("Blog post not found.", "danger")
        return redirect(url_for("blogs_page"))
    return render_template("blog_detail.html", post=post, posts=blog_posts)


# ======================
# Cart System
# ======================
@app.route("/add-to-cart/<int:pid>", methods=["POST"])
def add_to_cart(pid):
    product = get_product(pid)
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for("products_page"))

    qty_raw = request.form.get("qty", "1")
    try:
        qty = int(qty_raw)
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, min(10, qty))

    cart = session.get("cart", {})
    pid_key = str(pid)
    if pid_key in cart:
        cart[pid_key]["qty"] = min(10, int(cart[pid_key].get("qty", 1)) + qty)
    else:
        cart[pid_key] = {
            "name": product["name"],
            "price": float(product["price"]),
            "qty": qty,
            "hsn": product.get("hsn", ""),
            "gst_rate": float(product.get("gst_rate", 5)),
            "image": product.get("image", ""),
        }

    session["cart"] = cart
    session.modified = True
    flash(f"{product['name']} added to cart.", "success")
    return redirect(request.form.get("next") or request.referrer or url_for("cart_page"))


@app.route("/buy-now/<int:pid>", methods=["POST"])
def buy_now(pid):
    product = get_product(pid)
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for("products_page"))

    cart = session.get("cart", {})
    pid_key = str(pid)
    cart[pid_key] = {
        "name": product["name"],
        "price": float(product["price"]),
        "qty": 1,
        "hsn": product.get("hsn", ""),
        "gst_rate": float(product.get("gst_rate", 5)),
        "image": product.get("image", ""),
    }
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("checkout"))


@app.route("/wishlist-toggle/<int:pid>", methods=["POST"])
def wishlist_toggle(pid):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    product = get_product(pid)
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for("products_page"))

    existing = WishlistItem.query.filter_by(
        user_id=session["user_id"],
        product_id=pid
    ).first()

    if existing:
        db.session.delete(existing)
        flash("Product removed from wishlist.", "info")
    else:
        db.session.add(WishlistItem(user_id=session["user_id"], product_id=pid))
        flash("Product added to wishlist.", "success")

    db.session.commit()
    return redirect(request.referrer or url_for("products_page"))


@app.route("/account")
def account():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    user_id = session["user_id"]
    user = db.session.get(User, user_id)
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    addresses = get_user_addresses(user_id)

    wishlist_records = WishlistItem.query.filter_by(user_id=user_id).order_by(WishlistItem.created_at.desc()).all()
    wishlist_products = []
    seen_product_ids = set()
    for record in wishlist_records:
        product = get_product(record.product_id)
        if product and product["id"] not in seen_product_ids:
            wishlist_products.append(product)
            seen_product_ids.add(product["id"])

    return render_template(
        "account.html",
        account_user=user,
        orders=orders,
        addresses=addresses,
        wishlist_products=wishlist_products,
        payment_methods=PAYMENT_METHODS,
        indian_states=INDIAN_STATES,
    )


@app.route("/account/address/add", methods=["POST"])
def add_account_address():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    user_id = session["user_id"]
    label = request.form.get("label", "").strip() or "Home"
    recipient_name = request.form.get("recipient_name", "").strip()
    phone = normalize_phone(request.form.get("phone", ""))
    address_line = request.form.get("address_line", "").strip()
    city = request.form.get("city", "").strip()
    state = request.form.get("state", "").strip()
    pincode = request.form.get("pincode", "").strip()
    country = request.form.get("country", "India").strip() or "India"
    mark_default = request.form.get("is_default") == "on"

    if not recipient_name:
        flash("Please enter recipient name for address.", "danger")
        return redirect(url_for("account"))

    if not is_valid_phone(phone):
        flash("Please enter a valid mobile number for address.", "danger")
        return redirect(url_for("account"))

    address_error = validate_shipping_details(address_line, city, state, pincode, country)
    if address_error:
        flash(address_error, "danger")
        return redirect(url_for("account"))

    has_existing_address = UserAddress.query.filter_by(user_id=user_id).first() is not None
    if not has_existing_address:
        mark_default = True

    if mark_default:
        UserAddress.query.filter_by(user_id=user_id).update({"is_default": False})

    new_address = UserAddress(
        user_id=user_id,
        label=label[:50],
        recipient_name=recipient_name[:100],
        phone=phone[:20],
        address_line=address_line,
        city=city[:100],
        state=state[:80],
        pincode=pincode[:10],
        country="India",
        is_default=mark_default,
    )
    db.session.add(new_address)
    db.session.commit()
    flash("Address saved successfully.", "success")
    return redirect(url_for("account"))


@app.route("/account/address/default/<int:address_id>", methods=["POST"])
def set_default_address(address_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    user_id = session["user_id"]
    address = UserAddress.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        flash("Address not found.", "danger")
        return redirect(url_for("account"))

    UserAddress.query.filter_by(user_id=user_id).update({"is_default": False})
    address.is_default = True
    db.session.commit()
    flash("Default address updated.", "success")
    return redirect(url_for("account"))


@app.route("/account/address/delete/<int:address_id>", methods=["POST"])
def delete_account_address(address_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    user_id = session["user_id"]
    address = UserAddress.query.filter_by(id=address_id, user_id=user_id).first()
    if not address:
        flash("Address not found.", "danger")
        return redirect(url_for("account"))

    was_default = address.is_default
    db.session.delete(address)
    db.session.commit()

    if was_default:
        replacement = UserAddress.query.filter_by(user_id=user_id).order_by(UserAddress.created_at.desc()).first()
        if replacement:
            replacement.is_default = True
            db.session.commit()

    flash("Address removed.", "info")
    return redirect(url_for("account"))


@app.route("/cart")
def cart_page():
    cart = session.get("cart", {})
    total = money(0)
    totals = None
    if cart:
        totals = build_cart_totals(cart)
        total = totals["grand_total"]
    return render_template("cart.html", cart=cart, total=total, totals=totals)


@app.route("/remove-cart/<pid>")
def remove_cart(pid):
    cart = session.get("cart", {})
    if pid in cart:
        del cart[pid]
    session["cart"] = cart
    flash("Item removed from cart", "info")
    return redirect(url_for("cart_page"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty", "info")
        return redirect(url_for("products_page"))

    current_user = None
    user_addresses = []
    if "user_id" in session:
        current_user = db.session.get(User, session["user_id"])
        if current_user:
            user_addresses = get_user_addresses(current_user.id)

    totals = build_cart_totals(cart)
    total = totals["grand_total"]
    order_lines = [
        f"{item['name']} x {item['qty']} = Rs. {item['price'] * item['qty']}"
        for item in cart.values()
    ]
    order_summary = "ManviMart Order Enquiry\n\n"
    order_summary += "\n".join(order_lines)
    order_summary += f"\n\nTotal: Rs. {total}"
    order_summary += "\n\nCustomer name:\nPhone:\nDelivery address:"
    mail_subject = quote("ManviMart Order Enquiry")
    mail_body = quote(order_summary)

    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        customer_email = request.form.get("customer_email", "").strip().lower()
        customer_phone = normalize_phone(request.form.get("customer_phone", ""))
        selected_address_id = request.form.get("selected_address_id", "").strip()
        selected_address = None
        payment_method = request.form.get("payment_method", "").strip()

        if current_user:
            customer_name = customer_name or current_user.name
            customer_email = customer_email or current_user.email
            if not customer_phone and current_user.phone:
                customer_phone = normalize_phone(current_user.phone)

        if not customer_name or not customer_email or not customer_phone:
            flash("Please fill all contact details.", "danger")
            return redirect(url_for("checkout"))

        if payment_method not in PAYMENT_METHODS:
            flash("Please choose a valid payment method.", "danger")
            return redirect(url_for("checkout"))

        if not is_valid_phone(customer_phone):
            flash("Please enter a valid mobile number.", "danger")
            return redirect(url_for("checkout"))

        if current_user and selected_address_id and selected_address_id != "new":
            try:
                selected_address_pk = int(selected_address_id)
            except (TypeError, ValueError):
                flash("Please select a valid saved address.", "danger")
                return redirect(url_for("checkout"))

            selected_address = UserAddress.query.filter_by(
                id=selected_address_pk,
                user_id=current_user.id
            ).first()
            if not selected_address:
                flash("Selected address was not found.", "danger")
                return redirect(url_for("checkout"))

        if selected_address:
            shipping_address = selected_address.address_line
            shipping_city = selected_address.city
            shipping_state = selected_address.state
            shipping_pincode = selected_address.pincode
            shipping_country = selected_address.country
        else:
            shipping_address = request.form.get("shipping_address", "").strip()
            shipping_city = request.form.get("shipping_city", "").strip()
            shipping_state = request.form.get("shipping_state", "").strip()
            shipping_pincode = request.form.get("shipping_pincode", "").strip()
            shipping_country = request.form.get("shipping_country", "India").strip()

        shipping_error = validate_shipping_details(
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_state=shipping_state,
            shipping_pincode=shipping_pincode,
            shipping_country=shipping_country
        )
        if shipping_error:
            flash(shipping_error, "danger")
            return redirect(url_for("checkout"))

        totals = build_cart_totals(cart, shipping_state)
        invoice_no = f"MM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        tracking_id = f"MMT-{datetime.utcnow().strftime('%y%m%d')}-{uuid4().hex[:6].upper()}"
        order = Order(
            invoice_no=invoice_no,
            tracking_id=tracking_id,
            user_id=session.get("user_id"),
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_state=shipping_state,
            shipping_state_code=INDIAN_STATES[shipping_state],
            shipping_pincode=shipping_pincode,
            shipping_country="India",
            payment_method=payment_method,
            subtotal_amount=totals["subtotal"],
            taxable_amount=totals["taxable_total"],
            cgst_amount=totals["cgst_total"],
            sgst_amount=totals["sgst_total"],
            igst_amount=totals["igst_total"],
            gst_amount=totals["gst_total"],
            total_amount=totals["grand_total"],
            payment_status="Pending",
            order_status="Order Placed"
        )

        for item in totals["rows"]:
            order.items.append(OrderItem(
                product_id=item["pid"],
                product_name=item["name"],
                hsn_code=item["hsn"],
                gst_rate=item["gst_rate"],
                price=item["price"],
                quantity=item["quantity"],
                taxable_value=item["taxable"],
                cgst_amount=item["cgst"],
                sgst_amount=item["sgst"],
                igst_amount=item["igst"],
                line_total=item["line_total"]
            ))

        if current_user and not selected_address and request.form.get("save_new_address") == "on":
            make_default = request.form.get("set_default_address") == "on"
            has_existing_address = UserAddress.query.filter_by(user_id=current_user.id).first() is not None
            if not has_existing_address:
                make_default = True
            if make_default:
                UserAddress.query.filter_by(user_id=current_user.id).update({"is_default": False})
            new_address = UserAddress(
                user_id=current_user.id,
                label=(request.form.get("address_label", "").strip() or "Checkout")[:50],
                recipient_name=customer_name[:100],
                phone=customer_phone[:20],
                address_line=shipping_address,
                city=shipping_city[:100],
                state=shipping_state[:80],
                pincode=shipping_pincode[:10],
                country="India",
                is_default=make_default,
            )
            db.session.add(new_address)

        db.session.add(order)
        db.session.commit()

        send_order_alerts(order)

        session["cart"] = {}
        allowed_orders = session.get("allowed_order_ids", [])
        allowed_orders.append(order.id)
        session["allowed_order_ids"] = allowed_orders
        flash("Order placed successfully.", "success")
        return redirect(url_for("order_success", tracking_id=order.tracking_id))

    return render_template(
        "checkout.html",
        cart=cart,
        total=total,
        totals=totals,
        indian_states=INDIAN_STATES,
        payment_methods=PAYMENT_METHODS,
        order_summary=order_summary,
        mail_subject=mail_subject,
        mail_body=mail_body,
        current_user=current_user,
        user_addresses=user_addresses
    )


@app.route("/order-success/<tracking_id>")
def order_success(tracking_id):
    order = Order.query.filter_by(tracking_id=tracking_id).first_or_404()
    allowed_orders = session.get("allowed_order_ids", [])
    current_user_id = session.get("user_id")

    if order.user_id and order.user_id == current_user_id:
        pass
    elif order.id not in allowed_orders:
        flash("Please login to view this order.", "warning")
        return redirect(url_for("login"))

    whatsapp_link = None
    store_whatsapp = normalize_whatsapp_number(app.config.get("STORE_WHATSAPP_NUMBER", ""))
    if store_whatsapp:
        message = quote(
            f"Hi Manvi Mart, I placed an order.\nTracking ID: {order.tracking_id}\n"
            f"Name: {order.customer_name}\nPhone: {order.customer_phone}"
        )
        whatsapp_link = f"https://wa.me/{store_whatsapp}?text={message}"

    return render_template(
        "order_success.html",
        order=order,
        payment_methods=PAYMENT_METHODS,
        whatsapp_link=whatsapp_link
    )


@app.route("/track-order", methods=["GET", "POST"])
def track_order():
    order = None
    searched = False

    if request.method == "POST":
        searched = True
        tracking_id = request.form.get("tracking_id", "").strip().upper()
        phone = normalize_phone(request.form.get("phone", ""))
        order = Order.query.filter_by(tracking_id=tracking_id, customer_phone=phone).first()
        if not order:
            flash("Order not found. Please check your tracking ID and mobile number.", "danger")

    return render_template(
        "track_order.html",
        order=order,
        searched=searched,
        payment_methods=PAYMENT_METHODS
    )


@app.route("/invoice/<invoice_no>")
def invoice(invoice_no):
    order = Order.query.filter_by(invoice_no=invoice_no).first_or_404()
    allowed_orders = session.get("allowed_order_ids", [])
    current_user_id = session.get("user_id")

    if order.user_id and order.user_id == current_user_id:
        pass
    elif order.id not in allowed_orders:
        flash("Please login to view this invoice.", "warning")
        return redirect(url_for("login"))

    return render_template(
        "invoice.html",
        order=order,
        payment_methods=PAYMENT_METHODS
    )


# ======================
# Static Pages
# ======================
@app.route("/about")
def about():
    return render_template("pages/about.html")


@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")
        print(name,email,subject,message)
        flash("Message sent successfully!", "success")
        return redirect(url_for("contact"))
    return render_template("pages/contact.html")


@app.route("/privacy_policy")
def privacy_policy():
    return render_template("pages/privacy_policy.html")


@app.route("/return_policy")
def return_policy():
    return render_template("pages/return_policy.html")


@app.route("/terms_and_condition")
def terms_and_condition():
    return render_template("pages/terms_and_condition.html")


# ======================
# Signup
# ======================
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        phone = normalize_phone(request.form.get("phone"))
        password = request.form["password"]

        if not is_valid_phone(phone):
            flash("Please enter a valid mobile number.", "danger")
            return redirect(url_for("signup"))

        if not is_valid_password(password):
            flash("Password must be at least 8 characters long.", "danger")
            return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for("signup"))

        if User.query.filter_by(phone=phone).first():
            flash("Mobile number already registered!", "danger")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            phone=phone,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.id
        flash("Account created successfully!", "success")
        return redirect(safe_next_url())
    return render_template("auth/signup.html")


# ======================
# Login
# ======================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        identifier = request.form["identifier"].strip().lower()
        password = request.form["password"]

        user = User.query.filter(
            or_(User.email == identifier, User.phone == normalize_phone(identifier))
        ).first()

        if user and check_password_hash(user.password,password):
            session["user_id"] = user.id
            flash("Logged in successfully!", "success")
            return redirect(safe_next_url())
        flash("Invalid email/mobile or password!", "danger")
        return redirect(url_for("login"))
    return render_template("auth/login.html")


# ======================
# Logout
# ======================
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("home"))


# ======================
# Forgot Password
# ======================
@app.route("/forgot-password", methods=["GET","POST"])
def forgot_password():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        user = User.query.filter(
            or_(User.email == identifier, User.phone == normalize_phone(identifier))
        ).first()

        if user:
            token = serializer.dumps(user.email, salt="password-reset")
            reset_link = url_for(
                "reset_password",
                token=token,
                _external=True
            )
            if app.config['MAIL_USERNAME']:
                msg = Message(
                    "Password Reset - ManviMart",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[user.email]
                )
                msg.body = f"""
Hello {user.name},
Click the link below to reset your password:
{reset_link}
This link will expire in 10 minutes.
ManviMart Support
"""
                mail.send(msg)

            print("Password reset link:", reset_link)
            flash("If this account exists, a password reset link will be sent to the registered email.", "success")
            return redirect(url_for("login"))

        flash("If this account exists, a password reset link will be sent to the registered email.", "success")
        return redirect(url_for("login"))

    return render_template("auth/forgot_password.html")


# ======================
# Reset Password
# ======================
@app.route("/reset-password/<token>", methods=["GET","POST"])
def reset_password(token):
    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=600
        )
    except:
        flash("Reset link expired or invalid", "danger")
        return redirect(url_for("forgot_password"))
    user = User.query.filter_by(email=email).first()
    if request.method == "POST":
        new_password = request.form["password"]
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("reset_password", token=token))

        if not is_valid_password(new_password):
            flash("Password must be at least 8 characters long.", "danger")
            return redirect(url_for("reset_password", token=token))

        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("Password updated successfully!", "success")
        return redirect(url_for("login"))
    return render_template("auth/reset_password.html")


# ======================
# Run App
# ======================
if __name__ == "__main__":
    app.run()
