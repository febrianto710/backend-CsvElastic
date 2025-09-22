from flask import request, jsonify
import jwt
from functools import wraps
from config.settings import SECRET_KEY

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Ambil token dari header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"message": "Token tidak ditemukan"}), 401

        try:
            # Decode JWT
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = data  # Simpan data token ke request context
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token sudah kadaluarsa"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token tidak valid"}), 401

        return f(*args, **kwargs)
    return decorated
