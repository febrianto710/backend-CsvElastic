from flask import Flask, request, jsonify
import jwt
from datetime import datetime, timedelta
from flask_cors import CORS
import bcrypt
import os
from werkzeug.utils import secure_filename
import pandas as pd
from utils.index_documents import index_documents
from functools import wraps
from config.settings import  DEST_INDEX, IndexType
from database import engine, Base, get_db
from models.User import User

# Konfigurasi
app = Flask(__name__)
# DATABASE_URL = "mysql+pymysql://root:admin123@localhost/auth_db"
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
CORS(app)

Base.metadata.create_all(bind=engine)

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


@app.route("/login", methods=["POST"])
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


# Konfigurasi folder upload
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Fungsi cek ekstensi file
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-csv', methods=['POST'])
@token_required
def upload_csv():
    index_type = request.form.get('index_type')
    if not index_type:
        return jsonify({"error": "index type attribute tidak ada"}), 400
        
    if 'file' not in request.files:
        return jsonify({"error": "File belum di upload"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(filepath)
            file.save(filepath)
            out_filename = "output.csv"
            # menghapus kutip di awal dan akhir 
            with open(f'{filepath}', 'r') as f_in, open(out_filename, 'w') as f_out:
                for line in f_in:
                    # hapus tanda kutip " di awal dan akhir baris, dan hapus juga newline di akhir
                    cleaned_line = line.strip()
                    if cleaned_line.startswith('"') and cleaned_line.endswith('"'):
                        cleaned_line = cleaned_line[1:-1]
                    f_out.write(cleaned_line + '\n')
                    
            data = pd.read_csv(out_filename, on_bad_lines='skip', low_memory=False)
            # df.to_csv("tmp.csv")
            print(index_type)
            if index_type == IndexType.EMPLOYEE.value:             
                result = index_documents(data, DEST_INDEX["employee"])
            else:               
                result = index_documents(data, DEST_INDEX["test"])
                
            # result = index_documents(data)
            os.remove(filepath)
            os.remove(out_filename)
            
            if result != True:
                return jsonify({"error": result}), 400
          
            return jsonify({"message": "Data berhasil dikirim ke Elastic"}), 200
        except Exception as error:
            print(error)
            return jsonify({"error": f"Terjadi error: {error}"}), 500
                
    else:
        return jsonify({"error": "Format file harus CSV"}), 400



if __name__ == "__main__":
    app.run(port=5000)
    # app.run(debug=True)