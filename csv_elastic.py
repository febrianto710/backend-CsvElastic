from flask import Flask
from flask_cors import CORS
from database.connection import engine, Base
from routes.index import bp as index_routes
from routes.auth import bp as auth_routes
from config.settings import API_VERSION

# Konfigurasi
app = Flask(__name__)

CORS(app)

Base.metadata.create_all(bind=engine)
# register blueprints
app.register_blueprint(index_routes, url_prefix=f"/api/{API_VERSION}")
app.register_blueprint(auth_routes, url_prefix=f"/api/{API_VERSION}/auth")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, threaded=True)
    # app.run(debug=True)