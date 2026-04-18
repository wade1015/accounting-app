from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 🔥 PostgreSQL 連線
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# 📦 資料表
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))  # income / expense
    amount = db.Column(db.Integer)
    category = db.Column(db.String(100))
    note = db.Column(db.String(200))
    created_at = db.Column(db.String(20))
    user_id = db.Column(db.Integer)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(100))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    note = db.Column(db.String(200))
    user_id = db.Column(db.Integer)

# 建表
with app.app_context():
    db.create_all()

# =========================
# 🔐 註冊
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed = generate_password_hash(password)

        user = User(username=username, password=hashed)

        try:
            db.session.add(user)
            db.session.commit()
        except:
            return "帳號已存在"

        return redirect("/login")

    return render_template("register.html")


# =========================
# 🔑 登入
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect("/")
        else:
            return "登入失敗"

    return render_template("login.html")


# =========================
# 🚪 登出
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# 📊 首頁（記帳）
# =========================
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    data = Record.query.filter_by(user_id=user_id).all()

    income = sum(r.amount for r in data if r.type == "income")
    expense = sum(r.amount for r in data if r.type == "expense")

    return render_template("index.html", data=data, income=income, expense=expense)


# =========================
# ➕ 新增記帳
# =========================
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        r = Record(
            type=request.form["type"],
            amount=int(request.form["amount"]),
            category=request.form["category"],
            note=request.form["note"],
            created_at=request.form["created_at"],
            user_id=session["user_id"]
        )

        db.session.add(r)
        db.session.commit()

        return redirect("/")

    return render_template("add.html")


# =========================
# 🗑️ 刪除記帳
# =========================
@app.route("/delete/<int:id>")
def delete(id):
    r = Record.query.get(id)
    db.session.delete(r)
    db.session.commit()
    return redirect("/")


# =========================
# 📅 預約（含防撞🔥）
# =========================
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    if request.method == "POST":
        date = request.form["date"]
        time = request.form["time"]

        # 🔥 防撞
        existing = Booking.query.filter_by(
            date=date,
            time=time,
            user_id=user_id
        ).first()

        if existing:
            bookings = Booking.query.filter_by(user_id=user_id).all()
            return render_template("booking.html", bookings=bookings, error="此時段已被預約")

        b = Booking(
            customer=request.form["customer"],
            date=date,
            time=time,
            note=request.form["note"],
            user_id=user_id
        )

        db.session.add(b)
        db.session.commit()

        return redirect("/booking")

    bookings = Booking.query.filter_by(user_id=user_id).all()
    return render_template("booking.html", bookings=bookings)


# =========================
# 🗑️ 刪除預約
# =========================
@app.route("/delete_booking/<int:id>")
def delete_booking(id):
    b = Booking.query.get(id)
    db.session.delete(b)
    db.session.commit()
    return redirect("/booking")


if __name__ == "__main__":
    app.run()
