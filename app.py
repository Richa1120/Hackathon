import flask
from flask import Flask,render_template, request,redirect,url_for,session,send_from_directory,jsonify
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import random
from flask_cors import CORS
import requests
import time
from plyer import notification
from threading import Thread

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, "MHM.sqlite3")
app.config['UPLOAD_FOLDER'] = 'images'
db = SQLAlchemy()
db.init_app(app)
app.secret_key="secretkey"
app.app_context().push()

#########################################-----------------DATABASE-------------------#####################################

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    # Relationships
    daily_goals = db.relationship('DailyGoal', backref='user', lazy=True)
    journal_entries = db.relationship('JournalEntry', backref='user', lazy=True)

# # 2. Daily Goals Model
class DailyGoal(db.Model):
    __tablename__ = 'daily_goals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# # 3. Journal Entries Model
class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    smile = db.Column(db.Text, nullable=False)
    dealing = db.Column(db.Text, nullable=False)
    thankful = db.Column(db.Text, nullable=False)
    forward = db.Column(db.Text, nullable=False)


db.create_all()

#########################################-----------------LOGIN/REGISTER-------------------#####################################

@app.route('/',methods=["GET","POST"])
def login():
    if request.method=="POST":
        eml=request.form["email"]
        pwd=request.form["pass"]
        user=User.query.filter_by(email=eml).first()
        if user is not None and eml==user.email and pwd==user.password:
            session['current_user']=True
            return(redirect(url_for("user",nme=user.username)))
        else:
            return render_template("login.html",message="Invalid credentials!",title='AlmaZen')
    return render_template("login.html",message=0,title="AlmaZen")

@app.route('/register',methods=["GET","POST"])
def signup(message=0):
    if request.method=="POST":
        usrnm=request.form["username"]
        eml=request.form["email"]
        pwd=request.form["password"]
        usr=User(username=usrnm,email=eml,password=pwd)
        db.session.add(usr)
        db.session.commit()
        return(redirect(url_for("login", message=0,title='AlmaZen')))
    return render_template("register.html",message=0,title="AlmaZen")

#########################################-----------------USER ROUTES-------------------#####################################

@app.route('/user/<nme>', methods=["GET", "POST"])
def user(nme):
    if session.get('current_user'):
        return render_template("user.html", name=nme)
    else:
        return(redirect(url_for("login")))

@app.route('/user/<nme>/about',methods=["GET"])
def about(nme):
    if session.get('current_user'):
        return render_template("about.html", name=nme)
    else:
        return(redirect(url_for("login")))

@app.route('/user/<nme>/contact', methods=["GET"])
def contact(nme):
    if session.get('current_user'):
        return render_template("contact.html", name=nme)
    else:
        return(redirect(url_for("login")))

#########################################-----------------FEATURES-------------------#####################################

@app.route('/<nme>/features',methods=["GET"])
def features(nme):
    if session.get('current_user'):
        return render_template("features.html", name=nme)
    else:
        return(redirect(url_for("login")))


@app.route('/user/<nme>/games', methods=["GET", "POST"])
def games(nme):
    if session.get('current_user'):
        return render_template('games.html', name=nme)
    else:
        return redirect(url_for("login"))

@app.route('/user/<nme>/music', methods=["GET", "POST"])
def music(nme):
    if session.get('current_user'):
        return render_template('music.html', name=nme)
    else:
        return redirect(url_for("login"))

@app.route('/user/<nme>/doodle', methods=["GET", "POST"])
def doodle(nme):
    if session.get('current_user'):
        return render_template('doodle.html', name=nme)
    else:
        return redirect(url_for("login"))

@app.route('/user/<nme>/videos', methods=["GET", "POST"])
def videos(nme):
    if session.get('current_user'):
        return render_template('videos.html', name=nme)
    else:
        return redirect(url_for("login"))

#########################################-----------------DAILY GOALS-------------------#####################################

# Daily Goals Page - List All Goals for Logged In User
@app.route('/user/<nme>/daily_goals', methods=["GET", "POST"])
def daily_goals(nme):
    if session.get('current_user'):
        user_id = session.get('current_user')
        
        # List all goals for the logged-in user
        goals = DailyGoal.query.filter_by(user_id=user_id).all()

        # Add new goal
        if request.method == "POST":
            goal_text = request.form.get('goalText')
            if goal_text:
                new_goal = DailyGoal(user_id=user_id, goal=goal_text)
                db.session.add(new_goal)
                db.session.commit()
                return redirect(url_for('daily_goals', nme=nme))
        
        return render_template('daily_goals.html', goals=goals, name=nme)
    else:
        return redirect(url_for("login"))

# Update Goal
@app.route('/user/<nme>/daily_goals/update/<int:id>', methods=['POST'])
def update_goal(nme, id):
    if session.get('current_user'):
        goal = DailyGoal.query.get_or_404(id)
        
        # Ensure the user can only update their own goals
        if goal.user_id == session.get('current_user'):
            goal_text = request.form.get('goalText')
            if goal_text:
                goal.goal = goal_text
                db.session.commit()
        return redirect(url_for('daily_goals', nme=nme))
    else:
        return redirect(url_for("login"))

# Delete Goal
@app.route('/user/<nme>/daily_goals/delete/<int:id>')
def delete_goal(nme, id):
    if session.get('current_user'):
        goal = DailyGoal.query.get_or_404(id)
        
        # Ensure the user can only delete their own goals
        if goal.user_id == session.get('current_user'):
            db.session.delete(goal)
            db.session.commit()
        return redirect(url_for('daily_goals', nme=nme))
    else:
        return redirect(url_for("login"))

#########################################-----------------JOURNALING-------------------#####################################

@app.route('/user/<nme>/journaling', methods=["GET", "POST"])
def journaling(nme):
    if "current_user" not in session:
        return redirect(url_for("login"))  # Redirect to login if not logged in

    # Fetch user's journal entries
    entries = JournalEntry.query.filter_by(user_id=session["current_user"]).order_by(JournalEntry.date.desc()).all()

    # Check if request is an AJAX/fetch request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "entries": [
                {
                    "date": entry.date.strftime('%Y-%m-%d'),
                    "smile": entry.smile,
                    "dealing": entry.dealing,
                    "thankful": entry.thankful,
                    "forward": entry.forward
                }
                for entry in entries
            ]
        })

    # Render full page for normal browser visits
    return render_template('journals.html', name=nme, entries=entries)


@app.route('/journaling/save_entry', methods=["POST"])
def save_entry():
    if "current_user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Ensure the request is JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    
    # Debugging: Print received data
    print("Received data:", data)

    # Validate required fields
    required_fields = ["smile", "dealing", "thankful", "forward"]
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Create new journal entry
    new_entry = JournalEntry(
        user_id=session["current_user"],
        smile=data["smile"],
        dealing=data["dealing"],
        thankful=data["thankful"],
        forward=data["forward"]
    )
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"message": "Entry saved successfully!"}), 201

#########################################-----------------NOTIFICATIONS-------------------#####################################

# List of affirmations
affirmations = [
    "You are doing great! Keep going! 😊",
    "Believe in yourself, you are capable of amazing things! ✨",
    "Every small step counts, keep moving forward! 💪",
    "You are loved and appreciated! ❤",
    "You have the power to create a great day! 🌟",
    "I am here in the present moment.",
    "I am safe and there’s nothing to worry about.",
    "I’m grateful for all the good things in life.",
    "I can overcome challenging things.",
    "This moment is wonderful.",
]

# Function to show system notification
def show_notification():
    affirmation = random.choice(affirmations)  # Pick a random affirmation
    notification.notify(
        title="Positive Affirmation 💖",
        message=affirmation,
        app_name="Mindfulness App",
        app_icon="D:/richa/MOPVC stuff/Hackathon/static/images/sample_640×426.ico",
        timeout=10  # Notification disappears after 10 seconds
    )

# Function to run notifications in a separate thread
def notification_loop():
    while True:
        show_notification()
        time.sleep(120)  # Wait for 60 seconds before showing the next notification

#########################################-----------------LOGOUT-------------------#####################################

@app.route('/logout')
def logout():
    session.pop('current_user', None)
    return redirect(url_for('login'))

if __name__=='__main__':
    # Start the notification loop in a separate thread
    notification_thread = Thread(target=notification_loop)
    notification_thread.daemon = True
    notification_thread.start()

    # Start the Flask app
    app.run(host="0.0.0.0", debug=True, port=5000)