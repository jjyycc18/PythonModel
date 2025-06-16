import numpy as np
import pandas as pd
import copy
import scipy
import math
import datetime
import os
import sys
import json
import ast
import re
from common import constants , db_models
from config import config
import dao.vm_dao as vm_dao
from statistics import mean
from util.space_util import make_dic_group_by_key_func
from net.space_request_client import HttpRequestClient
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import traceback
from http import HTTPStatus
from flask import Flask, request
from flask_restful import Resource, Api
from util import pylogger
from common.db_models import db_session_remove
from util import space_request_parser
from util import model_execute

pylogger.generate_space_logger()
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

app = Flask(__name__)
api = Api(app)

@scheduler.scheduled_job('cron', hour=config.delete_job['trigger_time'], id='delete_job_scheduler')
def delete_job_scheduler():
    try:
        current_datatime = datetime.datetime.now()
        delete_target_list = []
        delete_cnt = 0
        site = vm_dao.get_site_info()

        if site == 'test':
            # delete_target_list.extend(...)
            pass
        
        logger.info("delete job is completed.")
    except Exception as e:
        logger.info("delete job unexpected error occurred.")  

class ExecuteScript(Resource):
    def post(self):
        try:
            if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
                client_ip = request.environ['REMOTE_ADDR']
            else:
                client_ip = request.environ['HTTP_X_FORWARDED_FOR']

            logger.info(f"__init__.ExecutePythonScript called. client_ip={client_ip}")
            script, result_key, env = space_request_parser.parser_execute_python_script(self)
            result = model_execute.execute_script(script, result_key, env)
            logger.info(f"__init__.ExecutePythonScript completed. client_ip={client_ip}")
        except Exception as e:
            logger.info("__init__.ExecutePythonScript unexpected error occurred.")
            return str(traceback.format_exc()), HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            return result

class httpchk(Resource):
    def get(self):
        return "Pass"
    
api.add_resource(ExecuteScript, '/gan/executeScript')
api.add_resource(httpchk, '/httpchk')

@app.teardown_request
def shutdown_session(exception=None):
    db_session_remove()

if __name__ == '__main__':
    #app.run(threaded=True)
    app.run(port=5001, threaded=True)
    #app.run(host='127.0.0.1' ,port=8070, threaded=True)
