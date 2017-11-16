from flask import jsonify
from werkzeug.exceptions import HTTPException, default_exceptions


class JSONExceptionHandler(object):
    """
    This is a very simple class that is used to transform Flask default exceptions from
    HTML to JSON, which (if not transformed) would break clients that expect JSON

    Inspired by https://coderwall.com/p/xq88zg/json-exception-handler-for-flask
    """
    def __init__(self, app):
        self.init_app(app)

    def std_handler(self, error):
        response = jsonify(message=error.description)
        response.status_code = error.code if isinstance(error, HTTPException) else 500
        return response

    def init_app(self, app):
        self.register(HTTPException, app)
        for code, v in default_exceptions.items():
            self.register(code, app)

    def register(self, exception_or_code, app):
        app.errorhandler(exception_or_code)(self.std_handler)
