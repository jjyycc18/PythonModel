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
from app import virtual_sensor, app_common_function

logger = logging.getLogger(__name__)

def execute_script(script:str, result_key:str, env:str):
  logger.info(f'model_execute called, result_key={result_key}, env={env}')
  
  if env is None:
    env = 'PY37'
    
  param_dict = {
    "SCRIPT": script
    , "RESULT_KEY": result_key
  }

  multi_version_url = app_common_function.get_multi_version_url(env)
  rc = HttpRequestClient(multi_version_url + '/executeMultiVersionScript' , param_dict)
  result_dict = rc.get_result()

  logger.info(f'model_execute completed, result_dict={result_dict}')
  return result_dict[result_key]

































    
