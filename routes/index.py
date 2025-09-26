from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timedelta
import bcrypt
import os
from werkzeug.utils import secure_filename
import pandas as pd
from utils.index_documents import index_documents
from functools import wraps
from config.settings import  DEST_INDEX, IndexType, SECRET_KEY, ALGORITHM, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, REQUIRED_COLUMNS
from database.connection import  get_db
from models.User import User
from utils.fetch_documents import fetch_documents
from utils.jwt_handler import token_required
from utils.generate_radom import generate_code

bp = Blueprint("index", __name__)

# Fungsi cek ekstensi file
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload-csv', methods=['POST'])
@token_required
def upload_csv():
    index_type = request.form.get('index_type')
    if not index_type:
        return jsonify({"error": "index type attribute tidak ada"}), 400
            
    # print(data_file)
    if 'file' not in request.files:
        return jsonify({"error": "File belum di upload"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400

    if file and allowed_file(file.filename):
        filepath = "default.csv"
        out_filename = "default.csv"
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, f"f_{generate_code()}_{filename}")
            # print(filepath)
            file.save(filepath)
            out_filename = f"output_{generate_code()}.csv"
            # menghapus kutip di awal dan akhir 
            with open(f'{filepath}', 'r') as f_in, open(out_filename, 'w') as f_out:
                for line in f_in:
                    # hapus tanda kutip " di awal dan akhir baris, dan hapus juga newline di akhir
                    cleaned_line = line.strip()
                    if cleaned_line.startswith('"') and cleaned_line.endswith('"'):
                        cleaned_line = cleaned_line[1:-1]
                        
                    # hapus semua karakter '
                    cleaned_line = cleaned_line.replace("'", "").replace(",", ";")
                    
                    f_out.write(cleaned_line + '\n')
  
          
            data = pd.read_csv(out_filename, on_bad_lines='skip', sep=";")
            # data.to_csv("xx.csv")
            data.columns = data.columns.str.upper()
            
            if index_type == IndexType.EMPLOYEE.value: 
                # cari kolom yang hilang
                missing_cols = list(set(REQUIRED_COLUMNS[IndexType.EMPLOYEE.value]) - set(data.columns))
                if len(missing_cols) != 0:
                    print("Kolom yang hilang:", missing_cols)
                    return jsonify({"error": f"Required Columns : {" , ".join(missing_cols)}"}), 400 
                    
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
                missing_cols = list(set(REQUIRED_COLUMNS[IndexType.QUOTA_DUKCAPIL.value]) - set(data.columns))
                if len(missing_cols) != 0:
                    print("Kolom yang hilang:", missing_cols)
                    return jsonify({"error": f"Required Columns : {" , ".join(missing_cols)}"}), 400 
                # format id : SERVICE-UNIT-TANGGAL
                data["TANGGAL"] = pd.to_datetime(data["TANGGAL"], format='mixed',
                    dayfirst=True,           # Kalau tanggal dalam format DD-MM-YYYY
                    errors='coerce')        
                # ubah ke string format DD-MM-YYYY HH:mm:ss
                data["TANGGAL_STR"] = data["TANGGAL"].dt.strftime("%d-%m-%Y %H:%M:%S")
                data["TRX_ID"] = data["SERVICE"] + "-" + data["UNIT"] + "-" + data["TANGGAL_STR"]
                data = data.drop(columns=["TANGGAL_STR"], errors="ignore")     
                result = index_documents(data, DEST_INDEX["quota_dukcapil"])
            elif index_type == IndexType.WEB_PORTAL.value:  
                missing_cols = list(set(REQUIRED_COLUMNS[IndexType.WEB_PORTAL.value]) - set(data.columns))
                if len(missing_cols) != 0:
                    print("Kolom yang hilang:", missing_cols)
                    return jsonify({"error": f"Required Columns : {" , ".join(missing_cols)}"}), 400 
                
                data["NIK"] = data.apply(
                    lambda row: f'{row["NIK"]}', 
                    axis=1
                )
                data["NPP"] = data["USERNAME"].str[-5:]    
                data["CHANNEL_NAME"] = "WEB_PORTAL"
                data["@TIMESTAMP"] = data.apply(lambda row: f'{row["TANGGAL"]}+07:00', axis=1)

                data["@TIMESTAMP"] = pd.to_datetime(data["@TIMESTAMP"], format='mixed',
                    dayfirst=True,           # Kalau tanggal dalam format DD-MM-YYYY
                    errors='coerce')
                data["TANGGAL"] = data["@TIMESTAMP"]
                data["TANGGAL_STR"] = data["TANGGAL"].dt.strftime("%d-%m-%Y %H:%M:%S")
                data["TRX_ID"] = data.apply(
                    lambda row: f"{row['TANGGAL_STR']}{row['CHANNEL_NAME']}{row['NPP']}{row['NIK']}", 
                    axis=1
                )
                
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
                
                df_employee_data["NPP"] = df_employee_data["NPP"].str[-5:]

                merged = data.merge(
                    df_employee_data[["NPP", "UNIT3"]],
                    on="NPP",
                    how="left"
                )
                # merged.to_csv("merged.csv")

                # isi kolom UNIT, default "-" kalau tidak ada match
                merged["UNIT"] = merged["UNIT3"].fillna("-")

                merged = merged.drop(columns=["UNIT3", "NPP", "NO", "TANGGAL_STR"], errors="ignore")   
                            
                result = index_documents(merged, DEST_INDEX["web_portal"])
            else:
                # os.remove(filepath)
                # os.remove(out_filename)
                return jsonify({"message": "Pilihan Tidak Tersedia"}), 400 

            # os.remove(filepath)
            # os.remove(out_filename)
            
            if result != True:
                return jsonify({"error": result}), 400
            
            return jsonify({"message": "Data berhasil dikirim ke Elastic"}), 200
        except Exception as error:
            # if os.path.exists(filepath):
            #     os.remove(filepath)
                
            # if os.path.exists(out_filename):
            #     os.remove(out_filename)
                
            print("error---------")
            print(error)
            return jsonify({"error": f"Terjadi error: {error}"}), 500
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                
            if os.path.exists(out_filename):
                os.remove(out_filename)
    else:
        return jsonify({"error": "Format file harus CSV"}), 400
