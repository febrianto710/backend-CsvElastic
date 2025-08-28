# File ini hanya untuk generate password yang sudah di hash, dan tidak dipakai di file manapun
import bcrypt
password = "bni2025/"
hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hashed_pw)