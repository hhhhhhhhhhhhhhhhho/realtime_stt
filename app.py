from flask_server import start_threads
from flask_server import flask_server

if __name__ == '__main__':
    start_threads()  # HLS 및 STT 시작
    flask_server = flask_server()
    flask_server.socketio.run(flask_server.app, host='0.0.0.0', port=8889)
