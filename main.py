from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base
import jwt
from datetime import datetime, timedelta
from flask_cors import CORS
import bcrypt
import os
from werkzeug.utils import secure_filename
import pandas as pd
import io
from index_documents import index_documents


# Konfigurasi
app = Flask(__name__)
DATABASE_URL = "mysql+pymysql://root:admin123@localhost/auth_db"
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
CORS(app)
# ORM setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Model User
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    npp = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    password_version = Column(Integer, default=1)
    
# Model User
class UploadHistory(Base):
    __tablename__ = "upload_history"
    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

Base.metadata.create_all(bind=engine)

@app.route("/login", methods=["POST"])
def login():
  data = request.get_json()
  npp = data.get("npp")
  password = data.get("password")
  
  if not npp or not password:
    return jsonify({"error": "npp dan password wajib diisi"}), 400
  
  session = SessionLocal()
  user = session.query(User).filter_by(npp=npp).first()

  if not user:
      session.close()
      return jsonify({"error": "NPP atau password salah"}), 400

  # Verifikasi password
  if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
    session.close()
    return jsonify({"error": "NPP atau password salah"}), 400

  # Buat JWT Token
  payload = {
      "nama": user.nama,
      "npp": user.npp,
      "pwv": user.password_version,
      "exp": datetime.utcnow() + timedelta(hours=2)
  }
  token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
  session.close()

  return jsonify({"token": token}), 200


# Konfigurasi folder upload
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Fungsi cek ekstensi file
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "file belum di upload"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400

    if file and allowed_file(file.filename):
        try:
          filename = secure_filename(file.filename)
          filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
          
          file.save(filepath)
          data = pd.read_csv(filepath, on_bad_lines='skip')
          # data.to_csv("tmp.csv")
          index_documents(data)
          os.remove(filepath)
          
          return jsonify({"message": "Data berhasil dikirim ke Elastic"}), 200
        except Exception as error:
          return jsonify({"error": error.message}), 500
                
    else:
        return jsonify({"error": "Format file harus CSV"}), 400



if __name__ == "__main__":
    app.run(debug=True)
    # app.run()