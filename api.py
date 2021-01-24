import os
import json
import hashlib
import shutil
import subprocess

from flask import Flask
from flask import request

from pathlib import Path

from marcell_sl_pipeline import MarcellPipeline


app = Flask(__name__)
marcell_pipeline = MarcellPipeline()


class InvalidParams(Exception):

    def __init__(self, message, status_code=500):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code


def check_form_data(text, meta):
    if text is None:
        raise InvalidParams('Missing "text" form data inside request.')

    if meta is None:
        raise InvalidParams('Missing "meta" form data inside request.')

    if text.isspace():
        raise InvalidParams('Form data inside "text" is empty.')

    if meta.isspace():
        raise InvalidParams('Form data inside "meta" is empty.')


@app.route('/annotate', methods=['POST'])
def run_pipeline():
    # Raw text for processing
    text = request.form.get('text')

    # Standoff metadata in JSON format
    meta = request.form.get('meta')

    # Check input validity
    check_form_data(text, meta)

    standoff_metadata = json.loads(meta)

    out = marcell_pipeline.process(text, standoff_metadata)
    return out, 200


@app.errorhandler(InvalidParams)
def handle_invalid_usage(error):
    return error.message, error.status_code


if __name__ == '__main__':
    app.run()

