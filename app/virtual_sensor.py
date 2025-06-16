import numpy as np
import pandas as pd
import copy
import scipy
import sklearn
import sklearn.gaussian_process
import math
import scipy
import datetime
import common.constants as constants
#import common.db_models as db_models
import dao.vm_dao as vm_dao
import os
import sys
import json
import ast
import re
import logging
from app.app_common_function import HttpRequestClient, get_multi_version_url
from app import mars_robot_hw

# mars_robot_hw 모듈의 함수들을 직접 가져옵니다
mars_time_robot = mars_robot_hw.mars_time_robot
mars_time_hw = mars_robot_hw.mars_time_hw

logger = logging.getLogger(__name__)

def generate_script(**kwargs):
    input_param_list = kwargs['input_param_list']
    input_data_list = kwargs['input_data_list']
    virtual_output_name = kwargs['virtual_output_name']
    script = kwargs['script']
    pre_defined_parameter_args = kwargs['pre_defined_parameter_args']
    result_name = kwargs['result_name']
    if virtual_output_name in script:
        script = script.replace(virtual_output_name, result_name)
    if input_param_list is not None and input_data_list is not None:
        for input_param, value in zip(input_param_list, input_data_list):
            if constants.DATA_2D == input_param.INPUT_TYPE or constants.OCD_2D == input_param.INPUT_TYPE:
                if isinstance(value, list):
                    for idx, val in enumerate(value):
                        input_name = '[{0}_{1}]'.format(input_param.DCOLL_ITEM, idx)
                        script = script.replace(input_name, str(val))
            input_name = '[' + input_param.DCOLL_ITEM + ']'
            if input_name in script:
                script = script.replace(input_name, str(value))
            input_name_2 = '[' + input_param.PROC_STEP_SEQ + ':' + input_param.DCOLL_ITEM + ']'
            if input_name_2 in script:
                script = script.replace(input_name_2, str(value))
            input_name_3 = '[' + str(input_param.INPUT_GROUP) + ':' + input_param.PROC_STEP_SEQ + ':' + input_param.DCOLL_ITEM + ']'
            if input_name_3 in script:
                script = script.replace(input_name_3, str(value))
    for param in constants.PRE_DEFINED_PARAMETER:
        input_name = '[' + param + ']'
        if input_name in script:
            script = script.replace(input_name, str(generate_pre_defined_param_value(param, pre_defined_parameter_args)))
    for param in constants.PRE_DEFINED_PARAMETER_WITH_VAR:
        for param_with_var in find_predefined_param_in_script(param, script):
            script = script.replace(param_with_var, str(generate_pre_defined_param_with_var(param_with_var, pre_defined_parameter_args)))
    if result_name == 'space_virtual_output_result':
        output_param_list = kwargs['output_param_list']
        output_data_list = kwargs['output_data_list']
        for output_param, value in zip(output_param_list, output_data_list):
            output_name = '[' + output_param.OUTPUT_NAME + ']'
            if output_name in script:
                script = script.replace(output_name, str(value))
    if '[reference_info_dict]' in script:
        script = script.replace('[reference_info_dict]', str(generate_pre_defined_param_value('[reference_info_dict]', pre_defined_parameter_args)))
    pmix_func_list = find_pmix_func_in_script(script)
    if pmix_func_list is not None and len(pmix_func_list) > 0:
        step_seq = generate_pre_defined_param_value('STEP_SEQ', pre_defined_parameter_args).replace('"', '')
        for pmix_func in pmix_func_list:
            script = script.replace(pmix_func, str(generate_pmix_func_result(pre_defined_parameter_args['lot_id'], pre_defined_parameter_args['wafer_id'], step_seq, pmix_func)))
    pmix_lot_list = find_pmix_lot_in_script(script)
    if pmix_lot_list is not None and len(pmix_lot_list) > 0:
        step_seq = generate_pre_defined_param_value('STEP_SEQ', pre_defined_parameter_args).replace('"', '')
        for pmix_lot in pmix_lot_list:
            script = script.replace(pmix_lot, str(generate_pmix_lot_dict(pre_defined_parameter_args['lot_id'], pre_defined_parameter_args['wafer_id'], step_seq, pmix_lot)))
    sleuth_order_script_list = find_sleuth_order_in_script(script)
    if sleuth_order_script_list is not None and len(sleuth_order_script_list) > 0:
        step_seq = generate_pre_defined_param_value('STEP_SEQ', pre_defined_parameter_args).replace('"', '')
        for sleuth_order_script in sleuth_order_script_list:
            script = script.replace(sleuth_order_script, str(generate_sleuth_order(pre_defined_parameter_args['lot_id'], pre_defined_parameter_args['wafer_id'], step_seq, sleuth_order_script)))
    return script
        
def generate_pre_defined_param_with_var(pre_defined_param, pre_defined_parameter_args):
    try:
        var_list = find_predefined_param_var(pre_defined_param)
        
        if not var_list or len(var_list) < 3:
            logger.error(f"Invalid var_list length: {len(var_list) if var_list else 0}")
            return None

        if 'MARS_TIME_ROBOT' in pre_defined_param:
            vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
            if not vm_model:
                logger.error("Failed to get vm_model")
                return None
                
            step_seq = vm_model.PROC_STEP_SEQ
            eqp_id = vm_model.EQP_ID
            lot_id = pre_defined_parameter_args['lot_id']
            wafer_id = pre_defined_parameter_args['wafer_id']
            src_var = var_list[0]
            dst_var = var_list[1]
            time_var = var_list[2]
            
            return mars_robot_hw.mars_time_robot(step_seq, eqp_id, lot_id, wafer_id, src_var, dst_var, time_var)

        if 'MARS_TIME_HW' in pre_defined_param:
            vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
            if not vm_model:
                logger.error("Failed to get vm_model")
                return None
                
            step_seq = vm_model.PROC_STEP_SEQ
            eqp_id = vm_model.EQP_ID
            lot_id = pre_defined_parameter_args['lot_id']
            wafer_id = pre_defined_parameter_args['wafer_id']
            work_var = var_list[0]
            state_var = var_list[1]
            time_var = var_list[2]
            
            return mars_robot_hw.mars_time_hw(step_seq, eqp_id, lot_id, wafer_id, work_var, state_var, time_var)
            
    except Exception as e:
        logger.exception(f"Error in generate_pre_defined_param_with_var: {str(e)}")
        return None        

def find_predefined_param_var(pre_defined_param):
    """Extract variables from predefined parameter string."""
    try:
        # Remove the predefined parameter prefix and split by underscore
        var_str = pre_defined_param.split('_', 3)[-1]
        return var_str.split('_')
    except Exception as e:
        logger.error(f"Error parsing predefined parameter: {str(e)}")
        return None

def generate_pre_defined_param_value(pre_defined_param, pre_defined_parameter_args):
    if pre_defined_param in ['EQP', 'EQP_ID']:
        vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
        return '"' + vm_model.EQP_ID + '"'
    if pre_defined_param in ['CH', 'CHAMBER_ID']:
        vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
        return '"' + vm_model.BIN + '"'
    if pre_defined_param in ['PPID']:
        if pre_defined_parameter_args['lot_track_seq'] != -1:
            vm_lot_track = vm_dao.get_vm_lot_track(pre_defined_parameter_args['lot_track_seq'])
            return '"' + vm_lot_track.PPID + '"'
        elif 'lot_id' in pre_defined_parameter_args.keys() and pre_defined_parameter_args['lot_id'] is not None:
            root_lot_id = app_common_function.generate_root_lot_id(pre_defined_parameter_args['lot_id'])
            vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
            tkin_info = vm_dao.get_lot_tkin_info(root_lot_id, vm_model.PROC_STEP_SEQ, int(pre_defined_parameter_args['wafer_id']))
            return '"' + tkin_info.PPID + '"'
    if pre_defined_param in ['INPUT_GROUP', 'INPUT_GROUP_NO']:
        return '"' + pre_defined_parameter_args['input_group'] + '"'
    if pre_defined_param in ['LOT_ID', 'LOT']:
        return '"' +pre_defined_parameter_args['lot_id']+ '"'
    if pre_defined_param in ['LINE_ID']:
        if pre_defined_parameter_args['lot_track_seq'] != -1:
            vm_lot_track = vm_dao.get_vm_lot_track(pre_defined_parameter_args['lot_track_seq'])
            return '"' + vm_lot_track.LINE_ID + '"'
        elif 'lot_id' in pre_defined_parameter_args.keys() and pre_defined_parameter_args['lot_id'] is not None:
            vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
            return '"' + vm_model.LINE_ID + '"'
    if pre_defined_param in ['DEVICE_ID', 'DEVICE']:
        if pre_defined_parameter_args['lot_track_seq'] != -1:
            vm_lot_track = vm_dao.get_vm_lot_track(pre_defined_parameter_args['lot_track_seq'])
            return '"' + vm_lot_track.DEVICE_ID + '"'
        elif 'lot_id' in pre_defined_parameter_args.keys() and pre_defined_parameter_args['lot_id'] is not None:
            vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
            return '"' + vm_model.DEVICE_ID + '"'
    if pre_defined_param in ['STEP_SEQ', 'PROC_STEP_SEQ']:
        if pre_defined_parameter_args['lot_track_seq'] != -1:
            vm_lot_track = vm_dao.get_vm_lot_track(pre_defined_parameter_args['lot_track_seq'])
            return '"' + vm_lot_track.PROC_STEP_SEQ + '"'
        elif 'lot_id' in pre_defined_parameter_args.keys() and pre_defined_parameter_args['lot_id'] is not None:
            vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
            return '"' + vm_model.PROC_STEP_SEQ + '"'
    if pre_defined_param in ['WF', 'WAFER_ID']:
        return '"' + pre_defined_parameter_args['wafer_id'] + '"'
    if pre_defined_param in ['INPUT_PARAM_DICT']:
        if 'input_group' in pre_defined_parameter_args.keys():
            return {param.ORDER_NO: param.DCOLL_ITEM for param in pre_defined_parameter_args['input_param_list'] if param.INPUT_GROUP == pre_defined_parameter_args['input_group']}
        else:
            return {param.ORDER_NO: param.DCOLL_ITEM for param in pre_defined_parameter_args['input_param_list']}
    if pre_defined_param in ['SIMAX_CH']:
        vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
        simax_ch = vm_dao.get_simax_chamber_id(vm_model.EQP_ID, vm_model.BIN)
        return '"' + simax_ch + '"'
    if pre_defined_param in ['TKOUT_TIME_STR']:
        vm_lot_track = vm_dao.get_vm_lot_track(pre_defined_parameter_args['lot_track_seq'])
        tkout_info = vm_dao.get_lot_tkout_info(vm_lot_track.LOT_ID, vm_lot_track.PROC_STEP_SEQ, vm_lot_track.EQP_ID)
        if tkout_info.LOT_TRANSN_TMSTP is not None:
            return tkout_info.LOT_TRANSN_TMSTP.strftime('%Y-%m-%d %H:%M:%S')
    if pre_defined_param in ['TMP_SEQ']:
        return pre_defined_parameter_args['tmp_seq']
    if pre_defined_param in ['MODEL_SEQ']:
        return pre_defined_parameter_args['model_seq']
    
    if pre_defined_param in ['[reference_info_dict]']:
        if pre_defined_parameter_args['lot_track_seq'] != -1:
            vm_lot_track = vm_dao.get_vm_lot_track(pre_defined_parameter_args['lot_track_seq'])
            tkout_info = vm_dao.get_lot_tkout_info(vm_lot_track.LOT_ID, vm_lot_track.PROC_STEP_SEQ, vm_lot_track.EQP_ID)
        elif 'lot_id' in pre_defined_parameter_args.keys() and pre_defined_parameter_args['lot_id'] is not None:
            lot_id = pre_defined_parameter_args['lot_id']
            vm_model = vm_dao.get_vm_model(pre_defined_parameter_args['model_seq'])
            tkout_info = vm_dao.get_lot_tkout_info(lot_id, vm_model.PROC_STEP_SEQ, vm_model.EQP_ID)
        reference_info_dict = dict()
        reference_info_dict['LOT_ID'] = tkout_info.LOT_ID
        reference_info_dict['STEP_SEQ'] = tkout_info.STEP_SEQ
        reference_info_dict['EQP'] = tkout_info.EQP_ID
        reference_info_dict['WF'] = pre_defined_parameter_args['wafer_id']
        reference_info_dict['TMP_SEQ'] = pre_defined_parameter_args['tmp_seq']
        reference_info_dict['MODEL_SEQ'] = pre_defined_parameter_args['model_seq']
        reference_info_dict['LINE_ID'] = tkout_info.LINE_ID
        reference_info_dict['DEVICE_ID'] = tkout_info.DEVICE_ID
        reference_info_dict['RUN_MODE'] = pre_defined_parameter_args['run_mode']
        if tkout_info.LOT_TRANSN_TMSTP is not None:
            reference_info_dict['TKOUT_TIME_STR'] = tkout_info.LOT_TRANSN_TMSTP.strftime('%Y-%m-%d %H:%M:%S')
        return reference_info_dict
    
    if pre_defined_param in ['PMIX_C-IDLE_TIME']:
        cur_step_seq = generate_pre_defined_param_value('STEP_SEQ', pre_defined_parameter_args).replace('"', '')
        cur_lot_info, pmix_lot_info = get_pmix_lot_info(pre_defined_parameter_args['lot_id'], pre_defined_parameter_args['wafer_id'], cur_step_seq,  constants.PMIX_STD_VARS_WF, constants.PMIX_ORDER_VARS_CHAMBER_END, constants.PMIX_SEARCH_VARS_EQP_CH)
        cur_lot_chamber_start_msg = vm_dao.get_chamber_start_msg_by_chamber_end(cur_lot_info.LOT_ID, cur_lot_info.WAFER_ID, cur_lot_info.EQP_ID, cur_lot_info.CHAMBER_ID, cur_lot_info.CREATE_TMSTP.strftime('%Y-%m-%d %H:%M:%S.%f'))
        cur_chamber_start_time_str = 'datetime.datetime({0}, {1}, {2}, {3}, {4}, {5})'.format(cur_lot_chamber_start_msg.CREATE_TMSTP.year, cur_lot_chamber_start_msg.CREATE_TMSTP.month, cur_lot_chamber_start_msg.CREATE_TMSTP.day, cur_lot_chamber_start_msg.CREATE_TMSTP.hour, cur_lot_chamber_start_msg.CREATE_TMSTP.minute, cur_lot_chamber_start_msg.CREATE_TMSTP.second)
        pmix_chamber_end_time_str = 'datetime.datetime({0}, {1}, {2}, {3}, {4}, {5})'.format(pmix_lot_info.CREATE_TMSTP.year, pmix_lot_info.CREATE_TMSTP.month, pmix_lot_info.CREATE_TMSTP.day, pmix_lot_info.CREATE_TMSTP.hour, pmix_lot_info.CREATE_TMSTP.minute, pmix_lot_info.CREATE_TMSTP.second)
        return eval(cur_chamber_start_time_str + ' - ' + pmix_chamber_end_time_str).total_seconds()
    if pre_defined_param in ['PMIX_W-IDLE_TIME']:
        cur_step_seq = generate_pre_defined_param_value('STEP_SEQ', pre_defined_parameter_args).replace('"', '')
        cur_lot_info, pmix_lot_info = get_pmix_lot_info(pre_defined_parameter_args['lot_id'], pre_defined_parameter_args['wafer_id'], cur_step_seq, constants.PMIX_STD_VARS_WF, constants.PMIX_ORDER_VARS_WAFER_END, constants.PMIX_SEARCH_VARS_EQP_CH)
        cur_lot_wafer_start_msg = vm_dao.get_wafer_start_msg_by_wafer_end(cur_lot_info.LOT_ID, cur_lot_info.WAFER_ID, cur_lot_info.EQP_ID, cur_lot_info.CREATE_TMSTP.strftime('%Y-%m-%d %H:%M:%S.%f'))
        cur_wafer_start_time_str = 'datetime.datetime({0}, {1}, {2}, {3}, {4}, {5})'.format(cur_lot_wafer_start_msg.CREATE_TMSTP.year, cur_lot_wafer_start_msg.CREATE_TMSTP.month, cur_lot_wafer_start_msg.CREATE_TMSTP.day, cur_lot_wafer_start_msg.CREATE_TMSTP.hour, cur_lot_wafer_start_msg.CREATE_TMSTP.minute, cur_lot_wafer_start_msg.CREATE_TMSTP.second)
        pmix_wafer_end_time_str =  'datetime.datetime({0}, {1}, {2}, {3}, {4}, {5})'.format(pmix_lot_info.CREATE_TMSTP.year, pmix_lot_info.CREATE_TMSTP.month, pmix_lot_info.CREATE_TMSTP.day, pmix_lot_info.CREATE_TMSTP.hour, pmix_lot_info.CREATE_TMSTP.minute, pmix_lot_info.CREATE_TMSTP.second)
        return eval(cur_wafer_start_time_str + ' - ' + pmix_wafer_end_time_str).total_seconds()
    if pre_defined_param in ['PMIX_IDLE_TIME']:
        cur_step_seq = generate_pre_defined_param_value('STEP_SEQ', pre_defined_parameter_args).replace('"', '')
        cur_lot_info, pmix_lot_info = get_pmix_lot_info(pre_defined_parameter_args['lot_id'], pre_defined_parameter_args['wafer_id'], cur_step_seq, constants.PMIX_STD_VARS_LOT, constants.PMIX_ORDER_VARS_TKOUT, constants.PMIX_SEARCH_VARS_EQP)
        cur_lot_tkin_info = vm_dao.get_lot_tkin_info(app_common_function.generate_root_lot_id(cur_lot_info.LOT_ID), cur_lot_info.STEP_SEQ, int(cur_lot_info.WAFER_ID))
        pmix_lot_tkout_info = vm_dao.get_lot_tkout_info(pmix_lot_info.LOT_ID, pmix_lot_info.STEP_SEQ, pmix_lot_info.EQP_ID)
        pmix_idle_time = cur_lot_tkin_info.LOT_TRANSN_TMSTP - pmix_lot_tkout_info.LOT_TRANSN_TMSTP
        return pmix_idle_time.total_seconds()
    