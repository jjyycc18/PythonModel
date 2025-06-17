from net.space_request_client import HttpRequestClient, HttpAsyncRequestClient
from config import config
import asyncio
import logging

logger = logging.getLogger(__name__)

def mp_dao_decorator(func):
  def func_wrapper(*args, **kwargs):
    loggerdebug("mp_dao.{0}, {1} e: {2}".format(func.__name__," unexpected exception occuered..", e))
    result = None
    try:
      result = func(*args, **kwargs)
    except Exception as e:
      loggerdebug("mp_dao.{0}, {1}".format(func.__name__," called.."))

    loggerdebug("mp_dao.{0}, {1}".format(func.__name__," completed.."))
    return result
  return func_wrapper

@mp_dao_decorator
def get_mp_input_data_list(tmp_seq, recipe_id, lot_id, wafer_id, site, input_group_no, order_no, option):
  param_dict = {
    "TMP_SEQ": temp_seq
    "RECIPE_ID": recipe_id
    "LOT_ID": lot_id
    "WAFER_ID": wafer_id
    "SITE": site
    "INPUT_GROUP_NO": input_group_no
    "ORDER_NO": order_no
    "OPTION": option
  }
  rc =  HttpRequestClient(config.mp['url'], param_dict, 6000)
  result = rc.get_result()
  return result

@mp_dao_decorator
def get_mp_input_data_list_async(mp_param_dict_list):
  async_rc = HttpAsyncRequestClient([config.mp['url']] * len(mp_param_dict_list),mp_param_dict_list, 3000)
  async_loop = asyncio.new_event_loop()
  result = async_loop.run_until_complete(async_rc.get_async_result())
  async_loop.close()      
  return result

if __name__ == '__main__':


















        
