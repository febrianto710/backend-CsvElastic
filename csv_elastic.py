from flask import Flask
from flask_cors import CORS
from database.connection import engine, Base
from routes.index import bp as index_routes
from routes.auth import bp as auth_routes
from config.settings import API_VERSION
from services.mail_service import mail

# Konfigurasi
app = Flask(__name__)
# DATABASE_URL = "mysql+pymysql://root:admin123@localhost/auth_db"
# Konfigurasi SMTP (contoh: Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'optimusprime200039@gmail.com'      # ganti dengan email kamu
app.config['MAIL_PASSWORD'] = 'poig wlen ehkv mhmd'         # gunakan app password, bukan password asli
app.config['MAIL_DEFAULT_SENDER'] = ('Portal Dukcapil', 'optimusprime200039@gmail.com')

# inisialisasi mail dengan app
mail.init_app(app)

CORS(app)

Base.metadata.create_all(bind=engine)
# register blueprints
app.register_blueprint(index_routes, url_prefix=f"/api/{API_VERSION}")
app.register_blueprint(auth_routes, url_prefix=f"/api/{API_VERSION}/auth")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
    # app.run(debug=True)