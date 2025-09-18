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
from database.connection import engine, Base, get_db
from models.User import User
from config.settings import es
from utils.fetch_documents import fetch_documents

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



@app.route('/upload-csv', methods=['POST'])
@token_required
def upload_csv():
    response_json = request.get_json()
    data = response_json.get("data")
    index_type = response_json.get('index_type')
    if not index_type:
        return jsonify({"error": "Jenis Data Tidak Ada"}), 400
    if len(data) <= 0:
        return jsonify({"error": "Tidak ada data yang dikirim"}), 400
    
    try:
          
        data = pd.DataFrame(data)
        # data = df.dropna()
        # data.to_csv(f"xx.csv")
        if index_type == IndexType.EMPLOYEE.value: 
            data["AS_OF_DATE"] = pd.to_datetime(data["AS_OF_DATE"], format='mixed',
                dayfirst=True,           
                errors='coerce')   
            data["TGL_LAHIR"] = pd.to_datetime(data["TGL_LAHIR"], format='mixed',
                dayfirst=True,           
                errors='coerce')    
            data["TGL_MASUK"] = pd.to_datetime(data["TGL_MASUK"], format='mixed',
                dayfirst=True,           
                errors='coerce')       
            result = index_documents(data, DEST_INDEX["employee"])
        elif index_type == IndexType.QUOTA_DUKCAPIL.value:  
            data["TRX_ID"] = data["tanggal"] + "_" + data["UNIT"] 
            data["tanggal"] = pd.to_datetime(data["tanggal"], format='mixed',
                dayfirst=True,           # Kalau tanggal dalam format DD-MM-YYYY
                errors='coerce')        
            result = index_documents(data, DEST_INDEX["quota_dukcapil"])
        elif index_type == IndexType.WEB_PORTAL.value:  
            data["NIK"] = data.apply(
                lambda row: f"{row["NIK"]}", 
                axis=1
            )
            data["NPP"] = data["USERNAME"].str[-5:]    
            data["CHANNEL_NAME"] = "WEB_PORTAL"
            data["TRX_ID"] = data.apply(
                lambda row: f"{row['TANGGAL']}{row['CHANNEL_NAME']}{row['NPP']}{row['NIK']}", 
                axis=1
            )
            data["@timestamp"] = data.apply(lambda row: f'{row["TANGGAL"]}+07:00', axis=1)

            data["@timestamp"] = pd.to_datetime(data["@timestamp"], format='mixed',
                dayfirst=True,           # Kalau tanggal dalam format DD-MM-YYYY
                errors='coerce')
            data["TANGGAL"] = data["@timestamp"]
            data["CHANNEL_ID"] = data["NPP"]
            data["SERVICE"] = "WEB PORTAL"
            data["NOMINAL"] = 1000
                
            query = {
                "query": {
                    "match_all": {}
                }
            }
            
            merged_data = []
            
            for batch in fetch_documents(query, DEST_INDEX["employee"]):
                for doc in batch:
                    source_data = doc["_source"]
                    merged_data.append(source_data)
                    
            df_employee_data = pd.DataFrame(merged_data)
            

            for index, row in data.iterrows():
                # cari data di kolom npp yang mengandung '553'
                filtered = df_employee_data[df_employee_data["NPP"].str.contains(row["NPP"], na=False)]
                if not filtered.empty:
                    
                    employee = filtered.iloc[0]
                    data.at[index, "UNIT"] = employee["UNIT3"] 
                    # print(row["UNIT"])
                else:
                    data.at[index, "UNIT"] = "-"    
            # data.to_csv("xx.csv")
            data = data.drop(columns=["NPP", "NO"])
                        
            result = index_documents(data, DEST_INDEX["web_portal"])
        else:

            return jsonify({"message": "Pilihan Tidak Tersedia"}), 400   

        
        if result != True:
            return jsonify({"error": result}), 400
        
        return jsonify({"message": "Data berhasil dikirim ke Elastic"}), 200
    except Exception as error:
        print("error---------")
        print(error)
        return jsonify({"error": f"Terjadi error: {error}"}), 500



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
    # app.run(debug=True)