import traceback
from http import HTTPStatus
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from multi_version_execute import multi_version_model_execute, multi_version_scrip_execute
import logging
from common import pylogger
from common.database import db_session_remove

pylogger.generate_space_logger()
logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)

def array_type(value,name):
  full_json_data = request.get_json()
  my_list = full_json_data[name]
  if not isinstance(my_list, (list)):
    raise ValueError("The parameter " + name + " is not a valid arry")
  return my_list  


class ExecuteMultiVersionModel(Resource):
  def port(self):
    try:
      parser = reqparse.RequestParser()
      parser.add_argument('MODEL_PATH')
      parser.add_argument('MODEL_CODE')
      parser.add_argument('PROBLEM_TYPE')
      parser.add_argument('INPUT_LIST', type=array_type, location='json')

      args = parser.parse_args()
      model_path =['MODEL_PATH']
      model_code =['MODEL_CODE']
      problem_type =['PROBLEM_TYPE']
      input_list =['INPUT_LIST']

      if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        client_ip = request.environ['REMOTE_ADDR']
      else:
        client_ip = request.environ['HTTP_X_FORWARDED_FOR']

      logger.info("multi_version_execute_init.ExecuteMutiVersionModel called.")  

      model = multi_version_model_execute.load_multi_version_model(model_path,model_code,problem_thpe)
      result = multi_version_model_execute.execute_multi_version_model(model, input_list)
      
      logger.info("multi_version_execute_init.ExecuteMutiVersionModel completed.")
    except Exception as e:
      logger.info("multi_version_execute_init unexpected error occurred.")
      return str(traceback.format_exc()), HTTPStatus.INTERNAL_SERVER_ERROR

    else:
      return result
      
class ExecuteMultiVersionScript(Resource):
  def port(self):
    try:
      parser = reqparse.RequestParser()
      parser.add_argument('SCRIPT')
      parser.add_argument('RESULT_KEY')

      args = parser.parse_args()
      script = args['SCRIPT']
      result_key =args['RESULT_KEY']

      if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        client_ip = request.environ['REMOTE_ADDR']
      else:
        client_ip = request.environ['HTTP_X_FORWARDED_FOR']

      logger.info("multi_version_execute_init.ExecuteMutiVersionModel called.")  

      result_dict = multi_version_script_execute.execute_multi_version_script(script)
      result = result_dict[result_key]
      
      logger.info("multi_version_execute_init.ExecuteMutiVersionModel completed.")
    except Exception as e:
      logger.info("multi_version_execute_init unexpected error occurred.")
      return str(traceback.format_exc()), HTTPStatus.INTERNAL_SERVER_ERROR

    else:
      return result
      
class httpchk(Resource):
  def get(self):
    return "Pass"
    
api.add_resource(ExecuteMultiVersionModel, '/executeMultiVersionModel')
api.add_resource(ExecuteMultiVersionScript, '/executeMultiVersionScript')
api.add_resource(httpchk, '/httpchk')

@app.teardown_request
def shutdoen_session(exception=None):
  db_session_remove()

if __name__ == '__main__':
  #app.run(threaded=True)
  app.run(port=7002, threaded=True)
  #app.run(host='127.0.0.1' ,port=8070, threaded=True)
