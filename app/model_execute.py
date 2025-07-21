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

#script 모델전부 대응
def execute_space_model_by_data(tmp_seq, input_dict, tmp_file_info_list, zone, input_param_dict, pre_defined_parameter_args):
    #kerasModel 계산
    output_list = []
    zones = list(zone.values())
    enviroment = vm.dao.get_vm_space_model_tmp_info(tmp_seq).ENVIROMENT

    cnt = 0
    for tmp_file_info in tmp_file_info_list :
        cnt += tmp_file_info.OUTPUT_CNT
    output_list = np.full((1,cnt), np.nan)
  
    try:
      for idx, tmp_file_info in enumerate(tmp_file_info_list):
        cur_zone, input_group_list = zone[idx]
        input_group = input_group_list[0]
        if tmp_file_info.MODEL_CODE in [constants.VIRTUAL_MODE]:
          pre_defined_parameter_args['input_group'] = input_group
          vittual_mode = vm_dao.get_virtual_model_script(tmp_file_info.GAN_FILE_SEQ)
          if input_dict in None and input_param_dict in None:
            output_list[:, cur_zone] = virtual_sensor.execute_space_virtuala_model(tmp_seq, virtual_model, None, None, pre_defined_parameter_args)
          else:
            output_list[:, cur_zone] = virtual_sensor.execute_space_virtuala_model(tmp_seq, virtual_model, input_dict[input_group], input_param_dict[input_group], pre_defined_parameter_args)
        else:
          if check_input_group(input_group_list, input_dict):
              if tmp_file_info.MODEL_CODE in [] or :
                virtual_model = vm_dao.get_virtual_model_script(tmp_file_info.GAN_FILE_SEQ)
                output_list[:, cur_zone] = virtual_sensor.execute_space_virtuala_model(tmp_seq, virtual_model, input_dict[input_group], input_param_dict[input_group], pre_defined_parameter_args)
              else:
                if len(input_group_list) > 1:
                  input_list = []
                  for input_group_no in input_group_list:
                    input_list.append(flatten_list(input_dict[input_group_no]))
                else:
                  input_list = flatten_list(input_dict[input_group_no])
                  
                param_dict = {"MODEL_PATH": generate_model_path(tmp_file_info)
                             ,"MODEL_CODE": tmp_file_info.MODEL_CODE
                             ,"PROBLEM_TYPE": tmp_file_info.PROBLEM_TYPE
                             ,"IMPUT_LIST": input_list
                             }
            
                multi_version_url = app_common_function.get_multi_virsion_url(enviroment)
                rc = HttpRequestClient(multi_virsion_url + '/executeMultiVersionModel' ,param_dic)
                multi_version_result = rc.get_result()
                output_list[:, cur_zone] = json.loads(multi_version_result)
          else:
            logger.info("input error")
      output_list = output_list.flatten()
      output_list = output_list.tolist()
      logger.info("execute_space_model_by_data completed")
      return output_list, None
  
    except Exception as e:
      logger.error(f"Error execute_space_model_by_data error: {str(e)}")
      return None, e  


















































    
