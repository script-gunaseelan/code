from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///housing.db'
app.config['SECRET_KEY'] = 'change-this-secret'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    income = db.Column(db.String(100), nullable=False)
    uploaded_file = db.Column(db.String(200), nullable=True)


def send_to_webhook(data, files=None):
    """Send form data and optional files to a webhook"""
    webhook_url = os.environ.get('WEBHOOK_URL')
    if not webhook_url:
        return
    try:
        requests.post(webhook_url, data=data, files=files or {})
    except Exception as exc:
        app.logger.error(f"Failed to send to webhook: {exc}")

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created, please log in')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    apps = Application.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', apps=apps)

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        full_name = request.form['full_name']
        income = request.form['income']
        file = request.files.get('document')
        filename = None
        file_path = None
        if file and file.filename:
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        application = Application(
            user_id=session['user_id'],
            full_name=full_name,
            income=income,
            uploaded_file=filename
        )
        db.session.add(application)
        db.session.commit()
        # Prepare data for webhook
        data = {'full_name': full_name, 'income': income, 'username': User.query.get(session['user_id']).username}
        files = {'document': open(file_path, 'rb')} if file_path else None
        send_to_webhook(data, files)
        if files:
            files['document'].close()
        flash('Application submitted')
        return redirect(url_for('dashboard'))
    return render_template('apply.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
