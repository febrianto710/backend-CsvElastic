
from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timedelta
import bcrypt
from config.settings import  SECRET_KEY, ALGORITHM, ELASTIC_URL_AUTH
import requests
from requests.auth import HTTPBasicAuth



bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["POST"])
def login():
  data = request.get_json()
  username = data.get("username")
  password = data.get("password")
  
  if not username or not password:
    return jsonify({"error": "username dan password wajib diisi"}), 400
  
  response = requests.get(
      ELASTIC_URL_AUTH,
      auth=HTTPBasicAuth(username, password),
      verify=False
  )
  
  if response.status_code == 200:
      user_info = response.json()
      # print(user_info)
      username = user_info.get("username","")
      # full_name = user_info.get("full_name", "")
      # email = user_info.get("email", "")
      # print(username)
      # print(full_name)
      
      # Buat JWT Token
      payload = {
          "username": username,
          # "full_name": full_name,
          # "pwv": user.password_version,
          "exp": datetime.utcnow() + timedelta(hours=2)
      }
      token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
      return jsonify({"token": token}), 200
  elif response.status_code == 401:
      return jsonify({"error": "username atau password salah"}), 401
  else:
      return jsonify({"error": "Internal Server Error"}), 500
