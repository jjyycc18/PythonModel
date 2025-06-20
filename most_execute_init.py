import traceback
from http import HTTPStatus
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from most_execute import most_execute
import logging
from common import pylogger
from common.database import db_session_remove

pylogger.generate_space_logger()
logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)

class InsertRawdata(Resource):
  def port(selt):
    try:
      parser = reqparse.RequestParser()
      parser.add_argument("RAWDATA_DICT")
      args = json.loads(json.dumps(parser.parse_args()))
      base_info_dict = json.loads(args["RAWDATA_DICT"])["BASE_INFO_DICT"]
      input_value_list = json.loads(args["RAWDATA_DICT"])["INPUT_VALUE_LIST"]
      output_value_list = json.loads(args["RAWDATA_DICT"])["OUTPUT_VALUE_LIST"]
  
      MOST_EXECUTE.INSERT_RAWDATA(base_info_dict , input_value_list, output_value_list)
    
    excetp Exception as e:
      return str(traceback.format_exc()), HTTPStatus.INTERNAL_SERVER_ERROR
    else:
      return None
     
class httpchk(Resource):
  def get(self):
    return "Pass"

@app.teardown_request
def shutdoen_session(exception=None):
  db_session_remove()

api.add_resource(InsertRawdata, '/insertRawdata')
api.add_resource(httpchk, '/httpchk')

if __name__ == '__main__':
  #app.run(threaded=True)
  app.run(port=7007, threaded=True)
  #app.run(host='127.0.0.1' ,port=8070, threaded=True)
