from flask import Flask, render_template, request, redirect, url_for, session, flash  # type: ignore
from flask_bcrypt import Bcrypt  # type: ignore
from pymongo import MongoClient  # type: ignore
from bson.objectid import ObjectId  # type: ignore
from datetime import datetime, date
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
bcrypt = Bcrypt(app)

# MongoDB connection using MongoClient
client = MongoClient("mongodb://localhost:27017/")  # local DB
db = client["Mental_Health_Assist"]   # Database

# Collections
users = db["Users"]               
schedules_collection = db["Scheduler"]
habits_collection = db["Habits"]
habit_logs = db["HabitLogs"]

@app.route("/")
def home():
    return render_template("Homepage.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if user exists
        if users.find_one({"username": username}):
            error = "Username already exists!"
            return redirect(url_for("register"))

        # Hash password & save
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        users.insert_one({"username": username, "password": hashed_pw})

        return redirect(url_for("login"))

    return render_template("register.html",error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = users.find_one({"username": username})
        if user and bcrypt.check_password_hash(user["password"], password):
            session["username"] = username
            return render_template("dashboard.html",username=session["username"])
        else:
            error = "Invalid Credentials!"
    return render_template("login.html",error=error)

@app.route("/dashboard")
def dashboard():
    if "username" in session:
        return render_template("dashboard.html", username=session["username"])
    return redirect(url_for("login"))

@app.route("/scheduler_dashboard")
def scheduler_dashboard():
    if "username" in session:
        schedules = list(schedules_collection.find())
        return render_template("scheduler_dashboard.html", schedules=schedules)
    return redirect(url_for("login"))

@app.route("/update_schedules/<schedule_id>",methods=["GET","POST"])
def update_scheduler(schedule_id):
    if "username" in session:
        schedules_collection.update_one(
            {"_id": ObjectId(schedule_id)},
            {"$set": {"status": "done"}}
        )
        return redirect(url_for("scheduler_dashboard"))
    return redirect(url_for("login"))

@app.route("/add_schedule", methods=["GET", "POST"])
def add_schedule():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        task = request.form.get("task")
        date = request.form.get("date")
        time = request.form.get("time")

        schedules_collection.insert_one({
            "task": task,
            "date": date,
            "time": time,
            "status": "pending"
        })

        return redirect(url_for("scheduler_dashboard"))

    return render_template("add_schedule.html")


@app.route("/routine_checker")
def routine_checker():
    if "username" in session:
        return render_template("dashboard.html",username=session["username"])
    return redirect(url_for("login"))

@app.route("/habits")
def habit_dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    habits = list(habits_collection.find({"user_id": ObjectId(user_id)}))
    return render_template("habit_dashboard.html", habits=habits)

@app.route("/add_habit", methods=["GET", "POST"])
def add_habit():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        habit_name = request.form.get("habit")
        if habit_name:
            habits_collection.insert_one({
                "user_id": ObjectId(user_id),   # link habit to user
                "habit": habit_name,
                "streak": 0,
                "temp_checked": False,
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            })
        return redirect(url_for("habit_dashboard"))
    return render_template("add_habit.html")

@app.route("/update_habit/<habit_id>", methods=["POST"])
def update_habit(habit_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    completed = "completed" in request.form  

    habit_logs.update_one(
        {"user_id": ObjectId(user_id), "habit_id": ObjectId(habit_id), "date": str(date.today())},
        {"$set": {"completed": completed}},
        upsert=True
    )

    return redirect(url_for("habit_dashboard"))


@app.route("/delete_habit/<habit_id>", methods=["POST"])
def delete_habit(habit_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    habits_collection.delete_one({"_id": ObjectId(habit_id), "user_id": ObjectId(user_id)})
    return redirect(url_for("habit_dashboard"))

def finalize_habits():
    today = datetime.now().strftime("%Y-%m-%d")
    habits = habits_collection.find()

    for habit in habits:
        last_date = habit.get("last_updated")
        checked = habit.get("temp_checked", False)

        update_data = {"temp_checked": False, "last_updated": today}

        if last_date != today:
            if checked:
                update_data["streak"] = habit["streak"] + 1
            else:
                update_data["streak"] = 0

            habits_collection.update_one({"_id": habit["_id"]}, {"$set": update_data})


@app.route("/chatbot")
def chatbot():
    if "username" in session:
        return render_template("dashboard.html",username=session["username"])
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
