from flask import Flask, render_template, request, flash, redirect, url_for, session, abort, make_response
import mysql.connector
import uuid
import hashlib
import qrcode
import os
import base64
from datetime import datetime
from flask_mail import Mail, Message
import csv 

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '#2819Thor'
app.config['MYSQL_DB'] = 'serv'

mysql = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        company_id = str(uuid.uuid4())
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM companies WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        cursor.close()
        if existing_user:
            return render_template('register.html', error_message="Email already registered. Please use a different email.")
        try:        
            cursor = mysql.cursor()
            cursor.execute("INSERT INTO companies (name, password, email, id) VALUES (%s, %s, %s, %s)", (username, hashed_password, email, company_id))
            mysql.commit()
            cursor.close()
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error creating company: {e}")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        cursor = mysql.cursor()
        cursor.execute("SELECT * FROM companies WHERE email = %s AND password = %s", (email, hashed_password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['user_id'] = user[2]
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        abort(403)  # Forbidden

    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logout successful!')
    return redirect(url_for('login'))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        abort(403)  

    if request.method == 'POST':
        product_name = request.form['product_name']
        description = request.form['description']
        user_id = session['user_id']  
        id = str(uuid.uuid4())
        cursor = mysql.cursor()
        cursor.execute("INSERT INTO products (name, description, id, user_id, time) VALUES (%s, %s, %s, %s, %s)", (product_name, description, id, user_id, datetime.now()))
        product_id = cursor.lastrowid
        mysql.commit()
        cursor.close()
        return redirect(url_for('product_list'))

    return render_template('add_product.html')

@app.route('/product_list')
def product_list():
    if 'user_id' not in session:
        abort(403)  

    user_id = session['user_id']
    cursor = mysql.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE user_id = %s", (user_id,))
    products = cursor.fetchall()
    cursor.close()

    for product in products:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"{product['name']} - {product['description']} - {product['time']} - {product['user_id']}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img_path = f"qrcode_{product['id']}.png"
        img.save(img_path)

        with open(img_path, "rb") as img_file:
            img_binary = img_file.read()
            product['qrcode'] = base64.b64encode(img_binary).decode('utf-8')

        os.remove(img_path)

    return render_template('product_list.html', products=products)

@app.route('/download_csv')
def download_csv():
    if 'user_id' not in session:
        abort(403)  

    user_id = session['user_id']
    cursor = mysql.cursor(dictionary=True)
    cursor.execute("SELECT name, description, time FROM products WHERE user_id = %s", (user_id,))
    products = cursor.fetchall()
    cursor.close()

    csv_data = []
    csv_data.append(','.join(['Product Name', 'Description', 'Time']))
    for product in products:
        csv_data.append(','.join([product['name'], product['description'], str(product['time'])]))

    response = make_response('\n'.join(csv_data))
    response.headers["Content-Disposition"] = "attachment; filename=products.csv"
    response.headers["Content-type"] = "text/csv"

    return response

if __name__ == '__main__':
    app.run(debug=True)


