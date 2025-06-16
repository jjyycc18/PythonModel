from net.space_request_client import HttpRequestClient
from config import config
from dao import gp_dao, vm_dao, bigdataquery_dao
from most_execute import most_common_function
import logging
import json
from app import redis_cache
from common import pylogger, constants

pylogger.generate_space_logger()
logger = logging.getLogger(__name__)

def all_most_apt(param_dict):
    site = vm_dao.get_site_info()
    if param_dict is None:
        return None

    try:
        param_dict = json.dumps(param_dict)
        most_url = config.most_executor["url"]

        rc = HttpRequestClient(most_url + '/insertRawdata', {"RAWDATA_DICT": param_dict}, 3)
        rc.get_result()

    except Exception as e:
        logger.exception("most_execute.call_most_apt : unexpected error occurred.")
    else:
        return None


def create_rm_data_list(rm_lot_info, redis_key):
    site = vm_dao.get_site_info()
    
    # 실계측값 조회, tmp별 센서 목록조회
    bigdata_result_list, tmp_metro_type_sensor_list = call_bigdata_query_api(rm_lot_info)

    if len(bigdata_result_list) == 0:
        # 4시간 지연조회
        if redis_key in []:
            redis_cache.set_most_rm_lot_info(rm_lot_info, constants.REDIS_MOST_KEY_RM_LOT_INFO_LIST_RETRY_1)
        return

    # insert row로 변화(tmp당 1개 row가되도록)
    rm_data_list = most_common_function.generate_most_rm_param_dict(bigdata_result_list, tmp_metro_type_sensor_list)

    # gpdb에 데이타저장
    insert_rm_data(rm_data_list)


def call_bigdata_query_api(rm_lot_info):
    site = vm_dao.get_site_info()
    
    # 조회 조건 세팅
    rm_lot_info = rm_lot_info.split("|")
    line_id, device_id, step_seq, lot_id, query_date = rm_lot_info[0], rm_lot_info[1], rm_lot_info[2], rm_lot_info[3], rm_lot_info[4].split(" ")[0]
    line_id = vm_dao.get_ivm_line(line_id).YMS_LINE_ID
    tmp_metro_type_sensor_list = vm_dao.get_tmp_metro_type_sensor_list(step_seq)
    metro_type_list = set(x.METRO_TYPE for x in tmp_metro_type_sensor_list)

    # metro type 별 각각 조회 후 result_list에 저장
    result_list = []
    if "FAB" in metro_type_list:
        table_name = 'fab.m_fab_wf_met'
        sensor_list = set(x.METRO_OUTPUT_NAME for x in tmp_metro_type_sensor_list if x.METRO_TYPE == "FAB")
        result_list.extend(bigdataquery_dao.get_y_fab_vm_data(table_name, line_id, query_date, sensor_list, step_seq, device_id, lot_id))

    return result_list, tmp_metro_type_sensor_list

def register_rm_lot_info(rm_lot_info):
    redis_cache.set_most_rm_lot_info(rm_lot_info, constants.REDIS_MOST_KEY_RM_LOT_INFO_LIST)

def insert_rawdata(base_info_dic, input_value_list, output_value_list):
    site = vm_dao.get_site_info()
    gp_dao.insert_vm_sm_tmp_most_raw(base_info_dic, input_value_list, output_value_list, site)

def insert_rm_data(rm_data_list):
    site = vm_dao.get_site_info()
    gp_dao.insert_vm_sm_tmp_most_rm(rm_data_list, site)

