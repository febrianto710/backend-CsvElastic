
from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timedelta
import bcrypt
from config.settings import  SECRET_KEY, ALGORITHM
from database.connection import  get_db
from models.User import User

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
