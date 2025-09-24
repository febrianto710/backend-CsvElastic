from database.connection import Base, engine, get_db
from models.User import User

Base.metadata.create_all(bind=engine)

db = get_db()
# hapus semua data User
db.query(User).delete()
db.commit()

users = [
          User(id=1, name="admin", email="dkcpl_admin@gmail.com", npp="1212", password="$2b$12$AnfLcixdbT8M364fpjUrO.xk.5CA/qOfeMIIJqtHD.XfRgDH3gYzG", password_version=1, is_activate=True, verification_code="444333"),
        ]

db.add_all(users)
db.commit()
db.close()