from flask import Flask

import logging
import os
import sys

from api.sign_url import sign_url_api


app = Flask(__name__)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-auth.json'

app.register_blueprint(sign_url_api)


if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    else:
        ip = '127.0.0.1'
        
    app.run(host=ip, port=5001, debug=True)
