from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Server is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def server_on():
    from threading import Thread
    t = Thread(target=run)
    t.start()
