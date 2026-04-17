from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
from flask import session


app = Flask(__name__)
app.secret_key = "your_secret_key"

# 建立資料庫
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        amount INTEGER,
        category TEXT,
        note TEXT,
        created_at TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        date TEXT,
        time TEXT,
        note TEXT,
        UNIQUE(date, time)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# 首頁（顯示資料）
@app.route("/")
def index():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM records")
    data = cursor.fetchall()

    type_map = {
        "income": "收入",
        "expense": "支出"
    }

    # ✅ 1. 基本統計
    income = sum(row[2] for row in data if row[1] == "income")
    expense = sum(row[2] for row in data if row[1] == "expense")


    # ✅ 2. 分類統計（圓餅圖用）
    category_data = {}
    for row in data:
        cat = row[3]
        category_data[cat] = category_data.get(cat, 0) + row[2]

    labels = list(category_data.keys())
    values = list(category_data.values())

    # ✅ 3. 月報表（Step 1）
    monthly_income = {}
    monthly_expense = {}

    for row in data:
        date = row[5]        # yyyy-mm-dd
        month = date[:7]     # yyyy-mm

        if row[1] == "income":
            monthly_income[month] = monthly_income.get(month, 0) + row[2]
        else:
            monthly_expense[month] = monthly_expense.get(month, 0) + row[2]

    # ✅ 4. Step 2（整理月份）
    all_months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))

    # ✅ 5. Step 3（轉成 list）
    income_list = [monthly_income.get(m, 0) for m in all_months]
    expense_list = [monthly_expense.get(m, 0) for m in all_months]

    conn.close()

    # ✅ 6. 最後才 return（所有資料都準備好）
    return render_template(
        "index.html",
        data=data,
        type_map=type_map,
        income=income,
        expense=expense,
        labels=labels,
        values=values,
        months=all_months,
        income_list=income_list,
        expense_list=expense_list
    )

# 新增資料
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        type_ = request.form["type"]
        amount = int(request.form["amount"])
        category = request.form["category"]
        note = request.form["note"]
        created_at = request.form["created_at"]

        #如果使用者沒填 > 用現在時間
        if not created_at:
            created_at = datetime.now().strftime("%Y-%m-%d")


        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO records (type, amount, category, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (type_, amount, category, note, created_at)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add.html")


#刪除資料
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM records WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

#預約頁面
@app.route("/booking", methods=["GET", "POST"])
def booking():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        customer = request.form["customer"]
        date = request.form["date"]
        time = request.form["time"]
        note = request.form["note"]

        # 🔥 檢查是否已有相同時段
        cursor.execute(
            "SELECT * FROM bookings WHERE date=? AND time=?",
            (date, time)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute("SELECT * FROM bookings ORDER BY date, time")
            bookings = cursor.fetchall()
            conn.close()

            return render_template("booking.html", bookings=bookings, error="此時段已被預約")

        # ✅ 沒撞到才新增
        cursor.execute(
            "INSERT INTO bookings (customer, date, time, note) VALUES (?, ?, ?, ?)",
            (customer, date, time, note)
        )
        conn.commit()

        return redirect("/booking")

    cursor.execute("SELECT * FROM bookings ORDER BY date, time")
    bookings = cursor.fetchall()

    conn.close()
    return render_template("booking.html", bookings=bookings)

#刪除預約資料
@app.route("/delete_booking/<int:id>")
def delete_booking(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bookings WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/booking")

#註冊功能
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        except:
            return "帳號已存在"

        conn.close()
        return redirect("/login")

    return render_template("register.html")

#登入功能
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect("/")
        else:
            return "登入失敗"

    return render_template("login.html")

#登出功能
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


if __name__ == "__main__":
    app.run()