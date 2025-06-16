from flask_restful import reqparse
from flask import request
import logging

logger = logging.getLogger(__name__)

def parser_execute_python_script():
    parser = reqparse.RequestParser()
    parser.add_argument('SCRIPT')
    parser.add_argument('RESULT_KEY')
    parser.add_argument('ENVIRONMENT')
    args = parser.parse_args()

    script = args['SCRIPT']
    result_key = args['RESULT_KEY']
    env = args['ENVIRONMENT']

    logger.info("parser_execute_python_script called")
    return script, result_key, env

