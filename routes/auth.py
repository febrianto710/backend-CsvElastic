
from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timedelta
import bcrypt
from config.settings import  SECRET_KEY, ALGORITHM
from database.connection import  get_db
from models.User import User
from utils.generate_radom import generate_code
from flask_mail import Mail, Message
from services.mail_service import mail

bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["POST"])
def login():
  data = request.get_json()
  npp = data.get("npp")
  password = data.get("password")
  
  if not npp or not password:
    return jsonify({"error": "npp dan password wajib diisi"}), 400
  
  db = get_db()
  user = db.query(User).filter_by(npp=npp).first()

  if not user:
      db.close()
      return jsonify({"error": "NPP atau password salah"}), 400

  # Verifikasi password
  if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
    db.close()
    return jsonify({"error": "NPP atau password salah"}), 400

  # Buat JWT Token
  payload = {
      "name": user.name,
      "npp": user.npp,
      "pwv": user.password_version,
      "exp": datetime.utcnow() + timedelta(hours=2)
  }
  token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
  db.close()

  return jsonify({"token": token}), 200

@bp.route("/register", methods=["POST"])
def register():
  try:
    json_data = request.get_json()
    name = json_data.get("name")
    npp = json_data.get("npp")
    email = json_data.get("email")
    password = json_data.get("password")
    print(json_data)
    db = get_db()
    user = db.query(User).filter_by(npp=npp).first()
    
    if user:
      return jsonify({"error": "NPP sudah dipakai, gunakan NPP lainnya"}), 400

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(generate_code())
    new_user = User(
        name=name,
        email=email,
        npp=npp,
        password=hashed_pw,
        is_activate=False,
        password_version=1,
        verification_code=generate_code(),
        expired_code=datetime.utcnow() + timedelta(minutes=15)
    )
    # tambahkan ke session
    # db.add(new_user)
    # db.commit()
    
    # Buat JWT Token
    payload = {
        "email": email,
        "npp": npp,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    msg = Message(
        subject="Hello from Flask",
        recipients=["ikxe496@gmail.com"],  # ganti penerima
        body="Ini email percobaan dari Flask-Mail"
    )
    mail.send(msg)
    return jsonify({"message": "Akun berhasil dibuat", "token": token}), 200
  except Exception as error:
    print("error---------")
    print(error)
    return jsonify({"error": f"Terjadi error: {error}"}), 500
  finally:
    db.close()