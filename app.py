from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv, find_dotenv
import os


app = Flask(__name__)
app.secret_key = "dev-key"

# 載入 .env
env_path = find_dotenv()
load_dotenv(env_path, override=True)

# Secret Key
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

# 開發環境先用 SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "test.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

print("目前使用資料庫：", app.config["SQLALCHEMY_DATABASE_URI"])

db = SQLAlchemy(app)


# =========================
# 🌐 語言翻譯字典
# =========================
translations = {
    "zh-TW": {
        "dashboard_title": "創業記帳 APP",
        "welcome": "歡迎",
        "add_record": "新增記帳",
        "record_list": "記帳列表",
        "booking": "預約系統",
        "monthly_report": "月統計表",
        "export_excel": "匯出 Excel",
        "settings": "設定",
        "logout": "登出",
        "back_dashboard": "回主控台",
        "save_settings": "儲存設定",
        "language_setting": "語言設定",
        "system_language": "系統語言",
        "appearance_setting": "外觀設定",
        "theme": "背景主題",
        "click_sound": "點擊音效",
        "background_music": "背景音樂",
        "click_volume": "點擊音量",
        "bg_volume": "背景音量"
    },
    "en": {
        "dashboard_title": "Business Accounting App",
        "welcome": "Welcome",
        "add_record": "Add Record",
        "record_list": "Record List",
        "booking": "Booking System",
        "monthly_report": "Monthly Report",
        "export_excel": "Export Excel",
        "settings": "Settings",
        "logout": "Logout",
        "back_dashboard": "Back to Dashboard",
        "save_settings": "Save Settings",
        "language_setting": "Language Settings",
        "system_language": "System Language",
        "appearance_setting": "Appearance Settings",
        "theme": "Theme",
        "click_sound": "Click Sound",
        "background_music": "Background Music",
        "click_volume": "Click Volume",
        "bg_volume": "Background Volume"
    },
    "vi": {
        "dashboard_title": "Ứng dụng kế toán kinh doanh",
        "welcome": "Xin chào",
        "add_record": "Thêm ghi chép",
        "record_list": "Danh sách ghi chép",
        "booking": "Hệ thống đặt lịch",
        "monthly_report": "Báo cáo tháng",
        "export_excel": "Xuất Excel",
        "settings": "Cài đặt",
        "logout": "Đăng xuất",
        "back_dashboard": "Quay lại bảng điều khiển",
        "save_settings": "Lưu cài đặt",
        "language_setting": "Cài đặt ngôn ngữ",
        "system_language": "Ngôn ngữ hệ thống",
        "appearance_setting": "Cài đặt giao diện",
        "theme": "Giao diện",
        "click_sound": "Âm thanh nhấp chuột",
        "background_music": "Nhạc nền",
        "click_volume": "Âm lượng nhấp chuột",
        "bg_volume": "Âm lượng nhạc nền"
    }
}





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

def get_text():
    language = session.get("language", "zh-TW")
    return translations.get(language, translations["zh-TW"])

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
    
    t = get_text()

    return render_template("register.html", t=t)


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
            return redirect("/dashboard")
        else:
            return "登入失敗"
        
    t = get_text()

    return render_template("login.html", t=t)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    t = get_text()

    return render_template("dashboard.html", t=t)


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

# =========================
# 📊 月報表
# =========================
    from collections import defaultdict

    income_map = defaultdict(int)
    expense_map = defaultdict(int)

    for r in data:
        if not r.created_at:
            continue

        month = r.created_at[:7]  # YYYY-MM

        if r.type == "income":
            income_map[month] += r.amount
        else:
            expense_map[month] += r.amount

    months = sorted(set(income_map.keys()) | set(expense_map.keys()))

    income_list = [income_map[m] for m in months]
    expense_list = [expense_map[m] for m in months]

    t = get_text()

    return render_template(
        "dashboard.html",
        t=t,
        data=data,
        income=income,
        expense=expense,
        months=months,
        income_list=income_list,
        expense_list=expense_list
    )


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
    
    t = get_text()

    return render_template("add.html", t=t)


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
            return render_template("booking.html", t=t, bookings=bookings, error="此時段已被預約")

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
    
    t = get_text()

    bookings = Booking.query.filter_by(user_id=user_id).all()
    return render_template("booking.html", t=t, bookings=bookings)


# =========================
# 🗑️ 刪除預約
# =========================
@app.route("/delete_booking/<int:id>")
def delete_booking(id):
    b = Booking.query.get(id)
    db.session.delete(b)
    db.session.commit()
    t = get_text()
    return redirect("/booking", t=t)
# ==========================
@app.route("/records")
def records():
    if "user_id" not in session:
        return redirect("/login")
    t = get_text()
    return render_template("records.html", t=t)



@app.route("/monthly-report")
def monthly_report():
    if "user_id" not in session:
        return redirect("/login")
    t = get_text()
    return render_template("monthly_report.html", t=t)


@app.route("/export")
def export():
    if "user_id" not in session:
        return redirect("/login")
    t = get_text()
    return render_template("export.html", t=t)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        session["language"] = request.form.get("language", "zh-TW")
        session["theme"] = request.form.get("theme", "beige")
        session["click_volume"] = request.form.get("click_volume", "50")
        session["bg_volume"] = request.form.get("bg_volume", "30")

        session["click_sound"] = "on" if request.form.get("click_sound") else "off"
        session["bg_music"] = "on" if request.form.get("bg_music") else "off"

        return redirect("/settings")
    
    t = get_text()

    return render_template(
        "settings.html",
        t=t,
        language=session.get("language", "zh-TW"),
        theme=session.get("theme", "beige"),
        click_volume=session.get("click_volume", "50"),
        bg_volume=session.get("bg_volume", "30"),
        click_sound=session.get("click_sound", "on"),
        bg_music=session.get("bg_music", "off")
    )

    
    

@app.route("/booking/public", methods=["GET", "POST"])
def booking_public():
    if request.method == "POST":
        # 之後這裡會處理客戶送出的預約資料
        return "預約已送出，之後可以改成成功頁面"
    
    t = get_text()

    return render_template("booking_public.html", t=t)

if __name__ == "__main__":
    app.run(debug=True)
