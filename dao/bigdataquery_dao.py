from common import fetch_data, constants
from config import config
from dao import vm_dao
from net.space_request_client import HttpRequestClient
import logging
import pandas as pd
logger = logging.getLogger(__name__)

def bigdataquery_decorator(func):
    def func_wrapper(*args, **kwargs):
        logger.info("bigdataquery_dao.{0} {1}".format(func.__name__, "called."))
        result = None
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.exception("bigdataquery_dao.{0} {1} : {2}".format(func.__name__, "unexpected exception occurred...", e))
        finally:
            pass
        logger.info("bigdataquery_dao.{0} {1}".format(func.__name__, "completed."))
        return result
    return func_wrapper

@bigdataquery_decorator
def get_eqp_robot_motion_history(line_name, eqp_id, lot_id, step_seq, start_date, end_date):
    query_param = {'table_name': 'fab.m_eqp_robot_motion_history',
                   'targetline': line_name,
                   'equipmentid': eqp_id,
                   'if_lot_id': lot_id,
                   'if_step_seq': step_seq,
                   'dateFrom': start_date,
                   'dateTo': end_date}
    custom_columns = ['area', 'equipmentid', 'srcmoduleid', 'srcmoduletype', 'srcslotno', 'state', 'starttime', 'endtime', 'dstmoduleid', 'dstmoduletype', 'dstslotno', 'materialid', 'starttime_rev', 'endtime_rev']
    param_dict = {'query_param': query_param, 'custom_columns': custom_columns}
    rc = HttpRequestClient(config.space_db_if_service['bigdataquery_getdata'], param_dict, 60 * 10 * 2)
    eqp_robot_motion_history_df = pd.read_json(rc.get_result(), dtype={'starttime': 'datetime64', 'endtime': 'datetime64', 'starttime_rev': 'datetime64', 'endtime_rev': 'datetime64' })
    return eqp_robot_motion_history_df

@bigdataquery_decorator
def get_eqp_hw_motion_history(line_name, eqp_id, module_id, work_group, start_date, end_date):
    query_param = {'table_name': 'fab.m_eqp_hw_motion_history',
                   'line_no': line_name,
                   'eqp_id': eqp_id,
                   'module_id': module_id,
                   'work_group': work_group,
                   'dateFrom': start_date,
                   'dateTo': end_date}
    custom_columns = ['eqp_id', 'module_id', 'work_group', 'state', 'start_time', 'end_time', 'material_id', 'starttime_rev', 'endtime_rev']
    param_dict = {'query_param': query_param, 'custom_columns': custom_columns}
    rc = HttpRequestClient(config.space_db_if_service['bigdataquery_getdata'], param_dict, 60 * 10 * 2)
    eqp_hw_motion_history_df = pd.read_json(rc.get_result(), dtype={'start_time': 'datetime64', 'end_time': 'datetime64', 'starttime_rev': 'datetime64', 'endtime_rev': 'datetime64' })
    return eqp_hw_motion_history_df
    
@bigdataquery_decorator
def get_eqp_hw_process_history(line_name, eqp_id, lot_id, step_seq, start_date, end_date):
    query_param = {'table_name': 'fab.m_fab_process',
                   'line_no': line_name,
                   'eqp_id': eqp_id,
                   'if_lot_id': lot_id,
                   'if_step_seq' : step_seq,
                   'work_group': 'PM',
                   'dateFrom': start_date,
                   'dateTo': end_date}
    custom_columns = ['eqp_id', 'module_id', 'work_group', 'state', 'start_time', 'end_time', 'material_id', 'starttime_rev', 'endtime_rev']
    param_dict = {'query_param': query_param, 'custom_columns': custom_columns}
    rc = HttpRequestClient(config.space_db_if_service['bigdataquery_getdata'], param_dict, 60 * 10 * 2)
    eqp_hw_motion_history_df = pd.read_json(rc.get_result(), dtype={'start_time': 'datetime64', 'end_time': 'datetime64' , 'starttime_rev': 'datetime64', 'endtime_rev': 'datetime64' })
    return eqp_hw_motion_history_df

@bigdataquery_decorator
def get_eqp_hw_p_idle_history(line_name, eqp_id, lot_id, step_seq, start_date, end_date):
    
    if line_name.startswith('P'):
        line_name = 'P'
    elif line_name.endswith('L'):
        line_name = line_name.rstrip('L')
        
    query_param = {'table_name': 'fab.m_fab_process',
                   'eqp_id': eqp_id,
                   'dateFrom': start_date,
                   'dateTo': end_date,
                   'like_conditions' : {'targetline' : f"%{line_name}%" }
                  }
    custom_columns = ['eqp_id', 'module_id', 'work_group', 'state', 'start_time', 'end_time', 'material_id', 'starttime_rev', 'endtime_rev','if_lot_id','if_step_seq']
    
    param_dict = {'query_param': query_param, 'custom_columns': custom_columns}
    
    rc = HttpRequestClient(config.space_db_if_service['bigdataquery_getdata'], param_dict, 60 * 10 * 2)
    eqp_hw_motion_history_df = pd.read_json(rc.get_result(), dtype={'start_time': 'datetime64', 'end_time': 'datetime64' , 'starttime_rev': 'datetime64', 'endtime_rev': 'datetime64' })
    
    return eqp_hw_motion_history_df

@bigdataquery_decorator
def get_eqp_hw_process_history(line_name, eqp_id, lot_id, step_seq, start_date, end_date):
    
    query_param = {'table_name': 'fab.m_fab_process',
                   'equipmentid': eqp_id,
                   'if_step_seq':step_seq,
                   'if_lot_id': lot_id,
                   'dateFrom': start_date,
                   'dateTo': end_date,
                   'like_conditions' : {'targetline' : f"%{line_name}%" }
                  }
    custom_columns = [ 'area', 'equipmentid', 'moduleid', 'workgroup', 'state', 'starttime', 'endtime', 'starttime_rev', 'endtime_rev', 'materialid', 'recipename', 'stepno', 'stepname',
                      'if_step_seq', 'if_lot_id', 'if_tkin_date' ]
    
    param_dict = {'query_param': query_param, 'custom_columns': custom_columns}
    
    rc = HttpRequestClient(config.space_db_if_service['bigdataquery_getdata'], param_dict, 60 * 10 * 2)
   hw_process_hist_df = pd.read_json(rc.get_result(), dtype={'start_time': 'datetime64', 'end_time': 'datetime64' , 'starttime_rev': 'datetime64', 'endtime_rev': 'datetime64' })
    
    return hw_process_hist_df
    
@bigdataquery_decorator
def get_fab_vm_data(table_name, line_id, device_id, step_seq, query_date):
    query_param = {'table_name': table_name,
                   'line_id': line_id,
                   'process_id': device_id,
                   'step_seq': step_seq,
                   'dateFrom': query_date,
                   'dateTo': query_date}
    custom_columns = ['line_id', 'process_id', 'step_seq', 'item_id']
    param_dict = {
        "query_param": query_param
        , "custom_columns": custom_columns
    }
    site = vm_dao.get_site_info()
    if site == constants.SITE_INFO_MEMORY:
        url = constants.C_BIG_URL_MEM
    elif site == constants.SITE_INFO_FOUNDRY:
        url = constants.C_BIG_URL_FDRY
    else:  # SCS
        url = constants.C_BIG_URL_SCS
    rc = HttpRequestClient(url, param_dict, 60 * 10 * 2)
    y_df = pd.read_json(rc.get_result())
    y_df = y_df.dropna(subset=['line_id', 'process_id', 'step_seq', 'item_id']).sort_values(by=['item_id'])
    y_df = y_df.drop_duplicates(subset=['line_id', 'process_id', 'step_seq', 'item_id'], keep='last')
    vm_data_list = []
    for idx, row in y_df.iterrows():
        vm_data_list.append(fetch_data.FetchData(
            ['line_id', 'device_id', 'step_seq', 'item_id'],
            [row['line_id'], row['process_id'], row['step_seq'], row['item_id']]))
    return vm_data_list
