from database import Base, engine, get_db
from models.User import User


Base.metadata.create_all(bind=engine)

db = get_db()

new_user = User(id=1, name="admin", npp="1212", password="$2b$12$AnfLcixdbT8M364fpjUrO.xk.5CA/qOfeMIIJqtHD.XfRgDH3gYzG", password_version=1)
db.add(new_user)
db.commit()