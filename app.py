from flask import Flask, render_template, request, session, redirect, flash, url_for, jsonify, send_from_directory
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import MySQLdb.cursors
import razorpay
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import hmac
import hashlib
import mediapipe as mp
from base64 import b64encode
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import urllib.request
from flask_cors import CORS
import http.client
import json
from urllib.parse import urlencode
# ... other imports ...

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

API_KEY = 'cm9dnraqw0002jl04289e0ymz'  # New API key

# Configuration
# --------------------------------------
# Secret key and mail configuration
app.secret_key = os.urandom(24)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Messipratham30'
app.config['MYSQL_DB'] = 'clothing_recommendations'
mysql = MySQL(app)

# Razorpay credentials
RAZORPAY_KEY_ID = "rzp_test_thbnstH0BXXXX"
RAZORPAY_KEY_SECRET = "oc86adrgm685ECs3WzdXXXX"
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Upload folder setup
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Initialize MediaPipe models
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1)
pose = mp_pose.Pose()

# Clothing Recommendations Data
# --------------------------------------
# Update the image paths to use local files


clothing_recommendations = {
    "male": {
        "hair_type": {
            "Long Hair": [
                {"id": 1, "name": "Slim Fit Shirt", "price": 29.99,
                 "image": "static/images/male/SlimFitShirt1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/SlimFitShirt1.jpg",
                 "material": "Cotton", "size": "M"},
                {"id": 2, "name": "Skinny Jeans", "price": 49.99,
                 "image": "static/images/male/SkinnyJeans1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/SkinnyJeans1.jpg",
                 "material": "Denim", "size": "32"}
            ],
            "Short Hair": [
                {"id": 3, "name": "Polo Shirt", "price": 24.99,
                 "image": "static/images/male/PoloShirt1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/PoloShirt1.jpg",
                 "material": "Polyester", "size": "L"},
                {"id": 4, "name": "Cargo Pants", "price": 39.99,
                 "image": "static/images/male/CargoPants1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/CargoPants1.jpg",
                 "material": "Cotton Blend", "size": "34"}
            ]
        },
        "face_shape": {
            "Oval Face": [
                {"id": 5, "name": "V-Neck Sweater", "price": 45.99,
                 "image": "static/images/male/V-NeckSweater1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/V-NeckSweater1.jpg",
                 "material": "Wool", "size": "M"},
                {"id": 6, "name": "Tailored Blazer", "price": 79.99,
                 "image": "static/images/male/TailoredBlazer1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/TailoredBlazer1.jpg",
                 "material": "Wool Blend", "size": "L"}
            ],
            "Round Face": [
                {"id": 7, "name": "Denim Jacket", "price": 59.99,
                 "image": "static/images/male/DenimJacket1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/DenimJacket1.jpg",
                 "material": "Denim", "size": "L"},
                {"id": 8, "name": "Crew Neck Sweater", "price": 39.99,
                 "image": "static/images/male/CrewNeckSweater1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/CrewNeckSweater1.jpg",
                 "material": "Cotton", "size": "XL"}
            ],
            "Square Face": [
                {"id": 9, "name": "Turtleneck Sweater", "price": 39.99,
                 "image": "static/images/male/TurtleneckSweater1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/TurtleneckSweater1.jpg",
                 "material": "Wool Blend", "size": "XL"},
                {"id": 10, "name": "Button-Up Shirt", "price": 34.99,
                 "image": "static/images/male/Button-UpShirt1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/Button-UpShirt1.jpg",
                 "material": "Cotton", "size": "M"}
            ]
        },
        "body_shape": {
            "Inverted Triangle Body": [
                {"id": 11, "name": "Fitted Blazer", "price": 89.99,
                 "image": "static/images/male/FittedBlazer1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/FittedBlazer1.jpg",
                 "material": "Wool", "size": "L"},
                {"id": 12, "name": "Slim Fit Chinos", "price": 49.99,
                 "image": "static/images/male/SlimFitChinos1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/SlimFitChinos1.jpg",
                 "material": "Cotton", "size": "34"}
            ],
            "Pear-Shaped Body": [
                {"id": 13, "name": "Straight Fit Jeans", "price": 49.99,
                 "image": "static/images/male/StraightFitJeans1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/StraightFitJeans1.jpg",
                 "material": "Denim", "size": "36"},
                {"id": 14, "name": "Patterned Shirt", "price": 39.99,
                 "image": "static/images/male/PatternedShirt1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/PatternedShirt1.jpg",
                 "material": "Cotton", "size": "L"}
            ],
            "Rectangular Body": [
                {"id": 15, "name": "Casual Button-Up", "price": 34.99,
                 "image": "static/images/male/CasualButton-Up1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/CasualButton-Up1.jpg",
                 "material": "Cotton", "size": "M"},
                {"id": 16, "name": "Fitted Sweater", "price": 44.99,
                 "image": "static/images/male/FittedSweater1.jpg",
                 "CLOTH_PRO": "static/cloth_pro/male/FittedSweater1.jpg",
                 "material": "Wool Blend", "size": "L"}
            ]
        }
    },
    "female": {
        "hair_type": {
            "Long Hair": [
                {"id": 17, "name": "Floral Dress", "price": 39.99,
                 "image": "static/images/floral_dress.jpg",
                 "CLOTH_PRO": "static/cloth_pro/floral_dress_pro.jpg",
                 "material": "Polyester", "size": "S"},
                {"id": 18, "name": "Maxi Skirt", "price": 29.99,
                 "image": "static/images/maxi_skirt.jpg",
                 "CLOTH_PRO": "static/cloth_pro/maxi_skirt_pro.jpg",
                 "material": "Cotton", "size": "M"}
            ],
            "Short Hair": [
                {"id": 19, "name": "Crop Top", "price": 19.99,
                 "image": "static/images/crop_top.jpg",
                 "CLOTH_PRO": "static/cloth_pro/crop_top_pro.jpg",
                 "material": "Cotton", "size": "S"},
                {"id": 20, "name": "High-Waisted Jeans", "price": 44.99,
                 "image": "static/images/high_waisted_jeans.jpg",
                 "CLOTH_PRO": "static/cloth_pro/high_waisted_jeans_pro.jpg",
                 "material": "Denim", "size": "28"}
            ]
        },
        "face_shape": {
            "Oval Face": [
                {"id": 21, "name": "Wrap Dress", "price": 49.99,
                 "image": "static/images/wrap_dress.jpg",
                 "CLOTH_PRO": "static/cloth_pro/wrap_dress_pro.jpg",
                 "material": "Polyester", "size": "M"},
                {"id": 22, "name": "V-Neck Blouse", "price": 29.99,
                 "image": "static/images/v_neck_blouse.jpg",
                 "CLOTH_PRO": "static/cloth_pro/v_neck_blouse_pro.jpg",
                 "material": "Silk", "size": "S"}
            ],
            "Round Face": [
                {"id": 23, "name": "V-Neck Top", "price": 24.99,
                 "image": "static/images/v_neck_top.jpg",
                 "CLOTH_PRO": "static/cloth_pro/v_neck_top_pro.jpg",
                 "material": "Cotton", "size": "S"},
                {"id": 24, "name": "A-Line Dress", "price": 39.99,
                 "image": "static/images/a_line_dress.jpg",
                 "CLOTH_PRO": "static/cloth_pro/a_line_dress_pro.jpg",
                 "material": "Cotton Blend", "size": "M"}
            ],
            "Square Face": [
                {"id": 25, "name": "Off-Shoulder Top", "price": 29.99,
                 "image": "static/images/off_shoulder_top.jpg",
                 "CLOTH_PRO": "static/cloth_pro/off_shoulder_top_pro.jpg",
                 "material": "Cotton Blend", "size": "M"},
                {"id": 26, "name": "Ruffled Blouse", "price": 34.99,
                 "image": "static/images/ruffled_blouse.jpg",
                 "CLOTH_PRO": "static/cloth_pro/ruffled_blouse_pro.jpg",
                 "material": "Polyester", "size": "S"}
            ]
        },
        "body_shape": {
            "Inverted Triangle Body": [
                {"id": 27, "name": "A-Line Skirt", "price": 34.99,
                 "image": "static/images/a_line_skirt.jpg",
                 "CLOTH_PRO": "static/cloth_pro/a_line_skirt_pro.jpg",
                 "material": "Polyester", "size": "M"},
                {"id": 28, "name": "Fitted Blazer", "price": 69.99,
                 "image": "static/images/fitted_blazer_f.jpg",
                 "CLOTH_PRO": "static/cloth_pro/fitted_blazer_f_pro.jpg",
                 "material": "Wool", "size": "S"}
            ],
            "Pear-Shaped Body": [
                {"id": 29, "name": "Flared Jeans", "price": 54.99,
                 "image": "static/images/flared_jeans.jpg",
                 "CLOTH_PRO": "static/cloth_pro/flared_jeans_pro.jpg",
                 "material": "Denim", "size": "28"},
                {"id": 30, "name": "Wrap Top", "price": 29.99,
                 "image": "static/images/wrap_top.jpg",
                 "CLOTH_PRO": "static/cloth_pro/wrap_top_pro.jpg",
                 "material": "Cotton", "size": "M"}
            ],
            "Rectangular Body": [
                {"id": 31, "name": "Belted Dress", "price": 49.99,
                 "image": "static/images/belted_dress.jpg",
                 "CLOTH_PRO": "static/cloth_pro/belted_dress_pro.jpg",
                 "material": "Cotton", "size": "S"},
                {"id": 32, "name": "Straight Leg Pants", "price": 44.99,
                 "image": "static/images/straight_leg_pants.jpg",
                 "CLOTH_PRO": "static/cloth_pro/straight_leg_pants_pro.jpg",
                 "material": "Polyester", "size": "6"}
            ]
        }
    }
}

# Create all_products list
all_products = []
for gender in clothing_recommendations.values():
    for category in gender.values():
        for items in category.values():
            all_products.extend(items)

# Utility Functions
# --------------------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_hair(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
    
    if len(faces) == 0:
        return "Face not detected"
    
    (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])  # Largest face
    hair_region = image[max(0, y - h // 2):y, max(0, x - w // 4):x + w + w // 4]
    
    if hair_region.size == 0:
        return "Hair not detected"
    
    edges = cv2.Canny(hair_region, 50, 150)
    hair_edge_count = np.sum(edges > 0)
    
    threshold = 10000  # Adjusted based on testing
    return "Long Hair" if hair_edge_count > threshold else "Short Hair"

def analyze_face(image):
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_image)
    
    if not results.multi_face_landmarks:
        return "Face not detected"
    
    landmarks = results.multi_face_landmarks[0].landmark
    chin_y = landmarks[152].y  # Bottom of chin
    forehead_y = landmarks[10].y  # Top of forehead
    face_width = abs(landmarks[234].x - landmarks[454].x)  # Cheek-to-cheek
    face_height = abs(chin_y - forehead_y)
    
    ratio = face_width / face_height
    if ratio > 1.1:
        return "Oval Face"
    elif ratio > 0.9:
        return "Round Face"
    return "Square Face"

def analyze_body(image):
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_image)
    
    if not results.pose_landmarks:
        return "Body not detected"
    
    landmarks = results.pose_landmarks.landmark
    shoulder_width = abs(landmarks[11].x - landmarks[12].x)  # Left to right shoulder
    waist_width = abs(landmarks[23].x - landmarks[24].x)    # Left to right hip (approx. waist)
    hip_width = abs(landmarks[25].x - landmarks[26].x)      # Left to right hip
    
    if shoulder_width > hip_width * 1.1:
        return "Inverted Triangle Body"
    elif hip_width > shoulder_width * 1.1:
        return "Pear-Shaped Body"
    return "Rectangular Body"

def create_order(amount, currency="INR", receipt=None, notes=None):
    try:
        order = razorpay_client.order.create({
            "amount": amount,  
            "currency": currency,
            "receipt": receipt,
            "notes": notes,
        })
        return order
    except Exception as e:
        return {"error": str(e)}

def verify_payment_signature(payment_id, order_id, signature):
    try:
        payload = f"{order_id}|{payment_id}"
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return generated_signature == signature
    except Exception as e:
        return False

# Authentication Routes
# --------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user['id']
            return redirect(url_for('gender_selection'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html', title="Login", action_url=url_for('login'), 
                         button_text="Login", signup=False, show_confirm=False, 
                         signup_url=url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('signup'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username already exists!')
            return redirect(url_for('signup'))
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', 
                         (username, hashed_password))
            mysql.connection.commit()
            flash('Signup successful! Please log in.')
            return redirect(url_for('login'))

    return render_template('login.html', title="Sign Up", action_url=url_for('signup'), 
                         button_text="Sign Up", signup=True, show_confirm=True, 
                         login_url=url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        if user:
            token = s.dumps(email, salt='email-confirm')
            link = url_for('reset_password', token=token, _external=True)

            msg = Message('Password Reset Request', sender='noreply@domain.com', recipients=[email])
            msg.body = f"Click the link to reset your password: {link}"
            mail.send(msg)

            flash('An email with password reset instructions has been sent to your email.')
            return redirect(url_for('login'))
        else:
            flash('Email not found.')

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash('The reset link is invalid or has expired.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('reset_password', token=token))
        
        hashed_password = generate_password_hash(password)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE users SET password = %s WHERE email = %s', 
                      (hashed_password, email))
        mysql.connection.commit()

        flash('Your password has been reset successfully.')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

@app.route('/auth/google')
def google_login():
    flash('Google login is not implemented yet.')
    return redirect(url_for('login'))

@app.route('/auth/facebook')
def facebook_login():
    flash('Facebook login is not implemented yet.')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

# User Flow Routes
# --------------------------------------
@app.route('/gender', methods=['GET', 'POST'])
def gender_selection():
    if 'logged_in' not in session or not session['logged_in']:
        flash('Please log in first.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        gender = request.form.get('gender')
        session['gender'] = gender
        return redirect(url_for('home'))
    
    return render_template('gender_selection.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'logged_in' not in session:
        flash('Please log in to access the home page.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image file uploaded.')
            return render_template('index.html')

        file = request.files['image']
        if file.filename == '':
            flash('No file selected.')
            return render_template('index.html')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Store the uploaded image path in session
            session['user_uploaded_image'] = filepath

            image = cv2.imread(filepath)
            if image is None:
                flash('Error loading image.')
                return render_template('index.html')

            hair_type = analyze_hair(image)
            face_shape = analyze_face(image)
            body_shape = analyze_body(image)
            
            session['hair_type'] = hair_type
            session['face_shape'] = face_shape
            session['body_shape'] = body_shape

            return render_template('index.html', 
                                hair_type=hair_type, 
                                face_shape=face_shape, 
                                body_shape=body_shape)

    return render_template('index.html')

# Product and Recommendation Routes
# --------------------------------------
@app.route('/recommendations')
def recommendations():
    if 'logged_in' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))

    print("\nSession Data:")
    print(f"Gender: {session.get('gender')}")
    print(f"Hair: {session.get('hair_type')}")
    print(f"Face: {session.get('face_shape')}")
    print(f"Body: {session.get('body_shape')}\n")

    gender = session.get('gender')
    if not gender:
        flash('Please complete the analysis first')
        return redirect(url_for('home'))

    recommended_items = []
    
    if gender.lower() in [g.lower() for g in clothing_recommendations.keys()]:
        gender_key = [g for g in clothing_recommendations.keys() if g.lower() == gender.lower()][0]
        gender_recs = clothing_recommendations[gender_key]
        
        for attr in ['hair_type', 'face_shape', 'body_shape']:
            attr_value = session.get(attr)
            if attr_value and attr in gender_recs:
                matched_key = next((k for k in gender_recs[attr].keys() 
                                  if k.lower() == attr_value.lower()), None)
                if matched_key:
                    print(f"Found {len(gender_recs[attr][matched_key])} matches for {attr}={matched_key}")
                    recommended_items.extend(gender_recs[attr][matched_key])

    unique_items = []
    seen_ids = set()
    for item in recommended_items:
        if item['id'] not in seen_ids:
            seen_ids.add(item['id'])
            unique_items.append(item)

    if not unique_items and gender.lower() in [g.lower() for g in clothing_recommendations.keys()]:
        print("No specific matches, showing general recommendations")
        gender_key = [g for g in clothing_recommendations.keys() if g.lower() == gender.lower()][0]
        for category in clothing_recommendations[gender_key].values():
            for items in category.values():
                unique_items.extend(items)
        seen_ids = set()
        final_items = []
        for item in unique_items:
            if item['id'] not in seen_ids:
                seen_ids.add(item['id'])
                final_items.append(item)
        unique_items = final_items[:12]

    sort_option = request.args.get('sort', 'best_match')
    if sort_option == 'price_asc':
        unique_items.sort(key=lambda x: x['price'])
    elif sort_option == 'price_desc':
        unique_items.sort(key=lambda x: x['price'], reverse=True)

    print(f"\nReturning {len(unique_items)} recommendations\n")
    
    return render_template(
        'recommendations.html',
        clothes=unique_items,
        sort=sort_option,
        user_attrs={
            'gender': gender,
            'hair_type': session.get('hair_type'),
            'face_shape': session.get('face_shape'),
            'body_shape': session.get('body_shape')
        }
    )

@app.route('/product/<int:product_id>')
def product_page(product_id):
    product = None
    product_gender = None
    
    for gender in clothing_recommendations.keys():
        for category in clothing_recommendations[gender].values():
            for items in category.values():
                for item in items:
                    if item['id'] == product_id:
                        product = item
                        product_gender = gender
                        break
                if product:
                    break
            if product:
                break
        if product:
            break

    if product:
        related_products = []
        if product_gender:
            for category in clothing_recommendations[product_gender].values():
                for items in category.values():
                    related_products.extend(items[:2])
        
        related_products = [p for p in related_products if p['id'] != product_id][:4]
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT r.rating, r.review_text, u.username FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.product_id = %s", 
                      (product_id,))
        reviews = cursor.fetchall()
        cursor.close()
        
        return render_template('product_page.html', 
                            product=product, 
                            reviews=reviews, 
                            related_products=related_products)
    else:
        flash("Product not found.")
        return redirect(url_for('recommendations'))

@app.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    if 'logged_in' in session:
        user_id = session['user_id']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)", 
                      (user_id, product_id))
        mysql.connection.commit()
        cursor.close()
        flash('Added to your wishlist!')
    else:
        flash('Please log in to add items to your wishlist.')
    
    return redirect(url_for('product_page', product_id=product_id))

# Cart Management Routes
# --------------------------------------
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    
    product = None
    # Find the product in recommendations
    for gender in clothing_recommendations.values():
        for category in gender.values():
            for items in category.values():
                for item in items:
                    if item['id'] == product_id:
                        product = item
                        break
                if product:
                    break
            if product:
                break
        if product:
            break

    if product:
        cart_item = {
            'id': product['id'],
            'name': product['name'],
            'price': float(product['price']),
            'image': product['image'],
            'quantity': 1
        }

        # Check if item already exists in cart
        item_exists = False
        for item in session['cart']:
            if item['id'] == product_id:
                item['quantity'] += 1
                item_exists = True
                break

        if not item_exists:
            session['cart'].append(cart_item)

        session.modified = True

        return jsonify({
            'success': True,
            'message': f"{product['name']} has been added to your cart",
            'cart_count': len(session['cart']),
            'cart_total': sum(item['price'] * item['quantity'] for item in session['cart'])
        })
    
    return jsonify({
        'success': False,
        'message': "Product not found"
    }), 404

@app.route('/update_quantity/<int:product_id>', methods=['POST'])
def update_quantity(product_id):
    action = request.form.get('action')
    
    if 'cart' in session:
        for item in session['cart']:
            if item['id'] == product_id:
                if action == 'increase':
                    item['quantity'] += 1
                elif action == 'decrease' and item['quantity'] > 1:
                    item['quantity'] -= 1
                break
    
    total = sum(item['price'] * item['quantity'] for item in session['cart'])
    session['total'] = total

    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
    
    return redirect(url_for('view_cart'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

@app.route('/clear_cart')
def clear_cart():
    try:
        session.pop('cart', None)
        flash('Cart cleared successfully.')
    except KeyError:
        flash('No cart found to clear.')
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
    return redirect(url_for('view_cart'))

# Checkout and Payment Routes
# --------------------------------------
@app.route('/buy_now/<int:product_id>', methods=['POST'])
def buy_now(product_id):
    product = None
    # Find the product in recommendations
    for gender in clothing_recommendations.values():
        for category in gender.values():
            for items in category.values():
                for item in items:
                    if item['id'] == product_id:
                        product = item
                        break
                if product:
                    break
            if product:
                break
        if product:
            break

    if product:
        session['checkout_item'] = {
            'id': product['id'],
            'name': product['name'],
            'price': float(product['price']),
            'image': product['image'],
            'quantity': 1
        }
        return redirect(url_for('checkout', product_id=product_id))
    
    flash("Product not found.")
    return redirect(url_for('recommendations'))

@app.route('/address', methods=['GET'])
def address():
    if 'checkout_item' not in session and 'cart' not in session:
        flash("Please proceed to checkout first.")
        return redirect(url_for('view_cart'))

    return render_template('address.html')

@app.route('/submit_address', methods=['POST'])
def submit_address():
    name = request.form.get('name')
    address = request.form.get('address')
    city = request.form.get('city')
    pincode = request.form.get('pincode')
    phone = request.form.get('phone')
    email = request.form.get('email')

    session['shipping_address'] = {
        'name': name,
        'address': address,
        'city': city,
        'pincode': pincode,
        'phone': phone,
        'email': email
    }

    return redirect(url_for('payment'))

@app.route('/payment')
def payment():
    if 'shipping_address' not in session:
        flash('Please enter your shipping address first.')
        return redirect(url_for('address'))

    if 'checkout_item' in session:
        cart = [session['checkout_item']]
        total = session['checkout_item']['price'] * session['checkout_item']['quantity']
    elif 'cart' in session and session['cart']:
        cart = session['cart']
        total = sum(item['price'] * item['quantity'] for item in cart)
    else:
        flash("Your cart is empty.")
        return redirect(url_for('view_cart'))

    return render_template('payment.html', cart=cart, total=total)

@app.route('/checkout')
def checkout_page():
    if 'checkout_item' in session:
        items = [session['checkout_item']]
        total = session['checkout_item']['price'] * session['checkout_item']['quantity']
    elif 'cart' in session and session['cart']:
        items = session['cart']
        total = sum(item['price'] * item['quantity'] for item in items)
    else:
        flash("Your cart is empty.")
        return redirect(url_for('view_cart'))

    return render_template('checkout.html', items=items, total=total)

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'shipping_address' in session:
        email = session['shipping_address'].get('email')
        name = session['shipping_address'].get('name')
        address = session['shipping_address'].get('address')
        city = session['shipping_address'].get('city')
        pincode = session['shipping_address'].get('pincode')

        if email:
            try:
                msg = Message('Order Confirmation',
                            sender='your-gmail@example.com',
                            recipients=[email])
                msg.body = f"Dear {name},\n\nYour order has been successfully placed.\n\nShipping to: {address}, {city}, {pincode}\n\nThank you for shopping with us!"
                mail.send(msg)
                flash('Confirmation email sent successfully!')
            except Exception as e:
                flash(f"Failed to send confirmation email: {str(e)}")

    flash('Your order has been placed successfully!')
    session.pop('cart', None)
    session.pop('checkout_item', None)

    return redirect(url_for('order_success'))

@app.route('/process_paypal', methods=['POST'])
def process_paypal():
    if 'cart' in session and 'shipping_address' in session:
        order_details = {
            'payment_method': 'PayPal',
            'cart_items': session['cart'],
            'shipping_address': session['shipping_address']
        }

        session.pop('cart', None)
        
        flash("Payment completed successfully via PayPal.")
        return redirect(url_for('order_success'))
    else:
        flash("There was an error with your order. Please try again.")
        return redirect(url_for('payment'))

@app.route('/process_cod', methods=['POST'])
def process_cod():
    session.pop('cart', None)
    session.pop('checkout_item', None)
    
    return redirect(url_for('order_success'))

@app.route('/create_order', methods=['POST'])
def handle_create_order():
    data = request.json
    amount = data.get('amount')
    currency = data.get('currency', 'INR')
    receipt = data.get('receipt')
    notes = data.get('notes')

    if not amount:
        return jsonify({"error": "Amount is required"}), 400

    order = create_order(amount, currency, receipt, notes)
    if "error" in order:
        return jsonify(order), 500

    return jsonify(order), 200

@app.route('/verify_razorpay_payment', methods=['POST'])
def verify_razorpay_payment():
    payment_data = request.get_json()
    
    session.pop('cart', None)
    session.pop('checkout_item', None)
    
    return jsonify({'success': True, 'redirect': url_for('order_success')})

@app.route('/payment_success', methods=['POST'])
def handle_payment_success():
    data = request.form
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    signature = data.get('razorpay_signature')

    if not all([payment_id, order_id, signature]):
        return jsonify({"error": "Missing required fields"}), 400

    is_valid = verify_payment_signature(payment_id, order_id, signature)
    if is_valid:
        return render_template('order_success.html', payment_id=payment_id, order_id=order_id)
    else:
        return jsonify({"status": "error", "message": "Invalid signature"}), 400

@app.route('/payment-success')
def payment_success():
    return redirect(url_for('order_success'))

@app.route('/order-success')
def order_success():
    return render_template('order_success.html')

@app.route('/try-on', methods=['POST'])
def try_on():
    if 'user_image' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    try:
        user_image = request.files['user_image']
        clothes_image = request.form.get('clothes_image')

        if not user_image or not clothes_image:
            return jsonify({'success': False, 'message': 'Missing required images'})

        # Create multipart form data
        encoder = MultipartEncoder(
            fields={
                'task_type': 'async',
                'clothes_type': 'upper_body',
                'person_image': ('person.jpg', user_image.stream, 'image/jpeg'),
                'clothes_image': ('clothes.jpg', open(clothes_image.lstrip('/'), 'rb'), 'image/jpeg')
            }
        )

        # Make API request
        print("Making try-on API request...")
        response = requests.post(
            'https://prod.api.market/api/v1/ailabtools/try-on-clothes/portrait/editing/try-on-clothes',
            data=encoder,
            headers={
                'x-magicapi-key': API_KEY,
                'Content-Type': encoder.content_type,
                'accept': 'application/json'
            },
            timeout=30
        )

        # Print response for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Body: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if data.get('error_code') == 0:
                return jsonify({
                    'success': True,
                    'task_id': data.get('task_id'),
                    'request_id': data.get('request_id')
                })
            else:
                return jsonify({
                    'success': False,
                    'message': data.get('error_msg', 'API returned an error'),
                    'error_code': data.get('error_code')
                })
        else:
            return jsonify({
                'success': False,
                'message': f'API request failed with status {response.status_code}',
                'response': response.text
            })

    except Exception as e:
        print(f"Try-on error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        })

@app.route('/check-try-on-status/<task_id>')
def check_try_on_status(task_id):
    try:
        print(f"Checking status for task: {task_id}")
        
        conn = http.client.HTTPSConnection("prod.api.market")
        headers = {
            'x-magicapi-key': API_KEY,
        }
        
        query_path = f"/api/v1/ailabtools/try-on-clothes/api/apimarket/query-async-task-result?task_id={task_id}"
        
        conn.request("GET", query_path, headers=headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode('utf-8'))
        
        print("Full API Response:")
        print(json.dumps(data, indent=2))

        # Check if we have a completed task with image
        if data.get('task_status') == 2 and data.get('data', {}).get('image'):
            return jsonify({
                'success': True,
                'status': 'completed',
                'image_url': data['data']['image'],
                'task_id': task_id,
                'raw_response': data
            })
        # Still processing
        elif data.get('task_status') == 1:
            return jsonify({
                'success': True,
                'status': 'processing',
                'task_id': task_id,
                'raw_response': data
            })
        # Error or unknown state
        else:
            return jsonify({
                'success': False,
                'status': 'error',
                'error_code': data.get('error_code'),
                'error_msg': data.get('error_msg', 'Unknown error'),
                'task_id': task_id,
                'raw_response': data
            })

    except Exception as e:
        print(f"Status check error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Status check error: {str(e)}',
            'task_id': task_id
        })

@app.route('/checkout/<int:product_id>')
def checkout(product_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # Get product details and render checkout page
    product = next((item for item in all_products if item['id'] == product_id), None)
    if not product:
        return redirect(url_for('recommendations'))
    
    return render_template('checkout.html', product=product)

# Main Execution
# --------------------------------------
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True, port=5000)