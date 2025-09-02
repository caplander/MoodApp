from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import locale
import os


app = Flask(__name__, instance_relative_config=True)
DB_PATH = os.path.join(app.instance_path, "moods.db")
app.secret_key = 'Milly'

# --- DATABASE CONFIG ---
db_path = os.path.join(app.instance_path, "moods.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# instance klasörü yoksa oluştur
os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy()
db.init_app(app)

# --- MODELS ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class MoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)  # "YYYY-MM-DD"
    color = db.Column(db.String(7), nullable=False)  # "#RRGGBB"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood_values = db.Column(db.String(50), nullable=False) 


# --- RENK FONKSİYONLARI ---
def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def average_hex_colors(hex1, hex2):
    rgb1 = hex_to_rgb(hex1)
    rgb2 = hex_to_rgb(hex2)
    avg_rgb = tuple((c1 + c2) // 2 for c1, c2 in zip(rgb1, rgb2))
    return "#{:02X}{:02X}{:02X}".format(*avg_rgb)

def average_multiple_hex_colors(hex_colors):
    total_r, total_g, total_b = 0, 0, 0
    count = 0
    for color in hex_colors:
        if color.startswith("#") and len(color) == 7:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            total_r += r
            total_g += g
            total_b += b
            count += 1
    if count == 0:
        return "#696969"
    avg_r = round(total_r / count)
    avg_g = round(total_g / count)
    avg_b = round(total_b / count)
    return '#{:02x}{:02x}{:02x}'.format(avg_r, avg_g, avg_b)


# --- ROUTES ---
@app.route('/')
def index():
    username = session.get('username')
    return render_template('index.html', username=username)


@app.route('/mood', methods=['GET', 'POST'])
def mood():
    response = None
    selected_moods_str = ""
    selected_moods = []
    username = session.get('username', 'misafir')
    user = None
    if username != 'misafir':
        user = User.query.filter_by(username=username).first()

    # --- Mood kategorileri ve renkler --- 
    mood_categories = {
        "pozitif": {
            "color": ["#A5D6A7", "#4CAF50", "#1B5E20"],
            "moods": ["Mutlu", "Huzurlu", "Rahat", "Minnettar", "Umutlu", "Coşkulu", "İlham almış", "Sevilmiş"]
        },
        "nötr": {
            "color": ["#90CAF9", "#2196F3", "#0D47A1"],
            "moods": ["Sıkılmış", "Boşlukta", "Kararsız", "Alakasız", "Dalgın", "Duyarsız", "Durgun", "Yorgun"]
        },
        "melankolik":{
             "color": ["#CE93D8", "#9C27B0", "#4A148C"],
             "moods": ["Hüzünlü", "İçine kapanık", "Özlem dolu", "Yalnız", "Kırgın", "Hayal kırıklığına uğramış", "Umutsuz", "Değersiz hissetmek"]
        },
        "stresli":{
             "color": ["#EF9A9A", "#F44336", "#B71C1C"],
             "moods": ["Endişeli", "Gergin", "Kızgın", "Kıskanç", "Suçlu", "Panik", "Bunalmış", "Kaygılı"]
        },
        "negatif":{
             "color": ["#FFCC80", "#FFC400", "#E68A00"],
             "moods": ["Tükenmiş", "Umursamaz", "Yetersiz", "Yalnızlık içinde", "Terkedilmiş", "Çaresiz", "İnatçı", "Kapanmak isteyen"]
        },
        "karışık":{
             "color": ["#6D6D6D", "#313131", "#000000"],
             "moods": ["Belirsiz", "Hem iyi hem kötü", "Tanımlanamayan", "Karmaşık", "Parçalanmış", "Belirsizlikten rahatsız"]
        }
    }

    def get_color_from_mood(mood):
        for category, cat_data in mood_categories.items():
            if mood in cat_data["moods"]:
                return cat_data["color"][1]  # orta tonu al
        return "#696969"

    mood_options = []
    for cat_data in mood_categories.values():
        mood_options.extend(cat_data["moods"])

    # Varsayılan olarak mood_color'ı gri (#696969) yapıyoruz
    mood_color = "#696969"  # Varsayılan değer


    if request.method == 'POST' and user:
        # 1. Formdan gelen string → liste
        selected_moods_str = request.form.get("moods", "")
        selected_moods     = selected_moods_str.split(",") if selected_moods_str else []

        if selected_moods:
            response = "Bugün kendini şöyle hissediyorsun: " + ", ".join(selected_moods)

            # 2. Seçilen ruh halleri renklerini al
            colors = [get_color_from_mood(m) for m in selected_moods]

            # 3. Kullanıcının geçmiş renklerini alıp birleştir
            previous_logs   = MoodLog.query.filter_by(user_id=user.id).all()
            previous_colors = [log.color for log in previous_logs]
            all_colors      = previous_colors + colors

            # 4. Tüm renklerin ortalamasını hesapla
            mood_color = average_multiple_hex_colors(all_colors)
            average_color = mood_color

            # 5. Bugünün tarihine göre eski log’u getir
            today = datetime.now().strftime("%Y-%m-%d")
            existing_log = MoodLog.query.filter_by(user_id=user.id, date=today).first()

            if existing_log:
                # 6a. Eski mood_values’i listeye çevir, yeni ekle, tekrar string’e çevir
                old_values = existing_log.mood_values or ""
                old_list   = [v for v in old_values.split(",") if v]
                combined   = old_list + selected_moods
                existing_log.mood_values = ",".join(combined)

                # 6b. Rengi de eski–yeni ortalamayla güncelle (opsiyonel)
                mood_color = average_hex_colors(existing_log.color, mood_color)
                existing_log.color = mood_color

            else:
                # 7. Yeni log’u oluştururken mood_values’i atamayı unutma
                new_log = MoodLog(
                    date=today,
                    color=mood_color,
                    user_id=user.id,
                    mood_values=selected_moods_str
                )
                db.session.add(new_log)

            # 8. Commit
            db.session.commit()

    return render_template('mood.html',response=response, username=username, mood_categories=mood_categories,
                           mood_options=mood_options, average_color=mood_color, mood_values=selected_moods_str)

@app.route('/profile')
def profile():
    username = session.get("username")
    if not username:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()
    today = datetime.now().date()
    dates = [(today - timedelta(days=i)).isoformat() for i in range(27, -1, -1)]
    colors = []

    for d in dates:
        log = MoodLog.query.filter_by(user_id=user.id, date=d).first()
        colors.append(log.color if log else "#d3d3d3")

    heatmap_data = list(zip(dates, colors))
    average_color = average_multiple_hex_colors(colors)
 
    return render_template("profile.html", username=username, dates=dates, colors=colors,
                           heatmap_data=heatmap_data, average_color=average_color)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        # Eğer kullanıcı varsa ve şifre doğruysa
        if user and user.check_password(password):
            session["username"] = user.username
            return redirect(url_for("profile"))
        else:
            return "Hatalı kullanıcı adı veya şifre."
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Aynı kullanıcı adı var mı kontrolü
        if User.query.filter_by(username=username).first():
            return "Bu kullanıcı adı zaten var"

        # Yeni kullanıcı oluşturuluyor
        new_user = User(username=username)
        new_user.set_password(password)  # Şifreyi hash'liyoruz
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/demo")
def demo():
    return render_template("demo.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))
from sqlalchemy.exc import IntegrityError



@app.route("/api/mood-data")
def mood_data():
    mood_entries = MoodLog.query.with_entities(MoodLog.date, MoodLog.color, MoodLog.mood_values).all()
    data = [{"date": entry.date, "color": entry.color, "moods": entry.mood_values} for entry in mood_entries]
    return jsonify({ "data": data })


@app.route("/api/mood-detail/<date>")
def mood_detail(date):
    user_id = session.get("user_id")
    entries = MoodLog.query.filter_by(user_id=user_id, date=date).all()

    result = []
    for entry in entries:
        result.append({
            "mood": entry.mood,})     

    return jsonify({ "date": date, "entries": result })

@app.route('/guides')
def guides():
    username = session.get('username', 'misafir')
    return render_template('guides.html', username=username)

if __name__ == "__main__": 
    app.run(debug=True)


