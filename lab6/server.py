import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request

log_handler = RotatingFileHandler("app.log", maxBytes=2048, backupCount=5)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
log_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        log_handler,
        logging.StreamHandler()
    ]
)

logging.getLogger('werkzeug').setLevel(logging.INFO)
logging.getLogger('server').setLevel(logging.INFO)

app = Flask(__name__)

@app.route('/hello')
def say_hello():
    app.logger.info('Handling /hello request')
    return "Hello, World!"

@app.route('/log')
def log_example():
    app.logger.debug("This is a DEBUG message")
    app.logger.info("This is an INFO message")
    app.logger.warning("This is a WARN message")
    app.logger.error("This is an ERROR message")
    return "Check logs for details!"

@app.route('/testError')
def generate_error():
    raise RuntimeError("Simulated error")

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"An error occurred: {str(e)}")
    return "Internal server error", 500

@app.before_request
def log_request_info():
    app.logger.info(f'HTTP Request: {request.method} {request.path}')

if __name__ == '__main__':
    app.run(debug=True)