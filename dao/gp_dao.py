from psycopg2.extras import Json
import logging
import config.config as config
from sqlalchemy import text
from common.database import gp_session

logger=logging.getLogger(__name__)

def gp_dao_session_decorator(func):
  def func_wrapper(*args, **kwargs):
    logger.debug("gp_dao.{0} {1}".format(func.__name__, "called."))
    Session = gp_session
    result = None
    try:
      with Session() as session, session.begin():
        result = func(session, *args, **kwargs)
    except Exception as e:
      logger.debug("gp_dao.{0} {1} e: {2}".format(func.__name__, "unexpected error occuered." , e))
    logger.debug("gp_dao.{0} {1}".format(func.__name__, "completed."))
    return result
  return func_wrapper

@gp_dao_session_decorator
def insert_vm_sm_tmp_most_raw(session, base_info_dict, input_value_list, output_value_list, site):
  if site == "MEM"
    table_name = "ivm_sm_tmp_most_raw_mem"
  else:
    table_name = "ivm_sm_tmp_most_raw_mem2"
    
  insert_list =[{"tmp_seq":base_info_dict["TEM_SEQ"],"tmp_seq2":base_info_dict["TEM_SEQ2"], "input_value_list": Json(input_value_list),"output_value_list": Json(output_value_list)  }]
  QUERY = "insert into " + table_name + " (tmp_seq,tmp_seq2, input_value_list,output_value_lis) values (:tmp_seq , :tmp_seq2 , input_value_list,output_value_list)"
  
  session.execute(text(query), insert_list)

if __name__ == "__main__":
  print('kk')
