from flask import Flask
from db import init_db
from routes import main

app = Flask(__name__)
app.secret_key = 'codigo-de-segunda-super-secreto'
app.register_blueprint(main)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)