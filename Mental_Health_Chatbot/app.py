from flask import Flask, render_template, request, redirect, url_for, session, flash # type: ignore
from flask_bcrypt import Bcrypt # type: ignore
from pymongo import MongoClient # type: ignore
from bson.objectid import ObjectId # type: ignore

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change in production
bcrypt = Bcrypt(app)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # local DB
db = client["Mental_Health_Assist"]   # Database
users = db["Users"]               # Collection for users
schedules_collection = db["Scheduler"]

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

@app.route("/habit_tracker")
def habit_tracker():
    if "username" in session:
        return render_template("dashboard.html",username=session["username"])
    return redirect(url_for("login"))

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
