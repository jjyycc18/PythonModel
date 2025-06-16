from common.database import pt_db_conn as db_conn, fdry_pt_db_conn as fdry_db_conn
from common.fetch_data import fetch_data_all, fetch_data_one
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def vm_dev_dao_session_decorator(func):
    def func_wrapper(*args, **kwargs):
        logger.debug("vm_dao.{0} {1}".format(func.__name__, "called."))
        conn = db_conn()
        session = conn.session()
        result = None
        try:
            result = func(session, *args, **kwargs)
        except Exception as e:
            logger.error("vm_dao.{0} {1} e : {2}".format(func.__name__, " unexpected exception occurred...", e))
        finally:
            session.close()
            conn.close()
        logger.debug("vm_dao.{0} {1}".format(func.__name__, "completed."))
        return result
    return func_wrapper

def vm_dao_decorator(func):
    def func_wrapper(*args, **kwargs):
        logger.debug("vm_dao.{0} {1}".format(func.__name__, "called."))
        conn = db_conn()
        cursor = conn.cursor()
        result_cursor = conn.cursor()
        result = None
        try:
            result = func(cursor, result_cursor, *args, **kwargs)
        except Exception as e:
            logger.error("vm_dao.{0} {1} e : {2}".format(func.__name__, " unexpected exception occurred...", e))
        finally:
            cursor.close()
            result_cursor.close()
            conn.close()
        logger.debug("vm_dao.{0} {1}".format(func.__name__, "completed."))
        return result
    return func_wrapper

def vm_dao_decorator2(func):
    def func_wrapper(*args, **kwargs):
        logger.debug("vm_dao.{0} {1}".format(func.__name__, "called."))
        conn = db_conn()
        cursor = conn.cursor()
        result = None
        try:
            result = func(conn, cursor, *args, **kwargs)
        except Exception as e:
            logger.error("vm_dao.{0} {1} e : {2}".format(func.__name__, " unexpected exception occurred...", e))
        finally:
            cursor.close()
            conn.close()
        logger.debug("vm_dao.{0} {1}".format(func.__name__, "completed."))
        return result
    return func_wrapper

def vm_dao_decorator3(func):
    def func_wrapper(*args, **kwargs):
        logger.debug("vm_dao.{0} {1}".format(func.__name__, "called."))
        if args[0] == 'MEM':
            conn = db_conn()
        else:
            conn = fdry_db_conn()
        cursor = conn.cursor()
        result_cursor = conn.cursor()
        result = None
        try:
            result = func(cursor, result_cursor, *args, **kwargs)
        except Exception as e:
            logger.error("vm_dao.{0} {1} e : {2}".format(func.__name__, " unexpected exception occurred...", e))
        finally:
            cursor.close()
            result_cursor.close()
            conn.close()
        logger.debug("vm_dao.{0} {1}".format(func.__name__, "completed."))
        return result
    return func_wrapper

@vm_dev_dao_session_decorator
def get_lot_tkout_info(session, lot_id, step_seq, eqp_id):
  query = "select line_id, ppid, device_id, step_seq, eqp_id, lot_id, lot_transn_tmstp from ivm_tkout where lot_id=:lot_id "
  session_result = session.execute(text(query), {"lot_id":lot_id})
  result = fetch_data_one(session_result,cursor)
  return result

@vm_dev_dao_session_decorator
def get_lot_tkin_info(session, lot_id, step_seq, eqp_id):
  query = "select line_id, ppid, device_id, step_seq, eqp_id, lot_id, lot_transn_tmstp from ivm_tkin where lot_id=:lot_id "
  session_result = session.execute(text(query), {"lot_id":lot_id})
  result = fetch_data_one(session_result,cursor)
  return result
  
@vm_dev_dao_session_decorator
def get_line_name(session, line_id):
  query = "select line_name from ivm_line where line_id=:line_id "
  session_result = session.execute(text(query), {"line_id":line_id})
  result = fetch_data_one(session_result,cursor)
  return result

@vm_dao_decorator
def get_site_info(cursor, result_cursor) :
    query = """
        SELECT SETNG_VALS FROM IVM_APP_CONFIG
         WHERE APP_NAME = 'COMMON' AND SETNG_NAME = 'SITE'
    """
    cursor.execute(query)
    result = fetch_data_one(cursor)
    return result.SETNG_VALS

@vm_dao_decorator
def def_vm_db_connect_test(cursor, result_cursor):
    query = """
        SELECT (SELECT name FROM v$database) AS DB_NAME
              ,LINE_ID ,LINE_NAME
          FROM IVM_LINE WHERE ROWNUM < 3
    """
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_vm_space_model_tmp_input_param(cursor, result_cursor, tmp_seq):
    query = "SELECT IP.TMP_SEQ, IP.PROC_STEP_SEQ, IP.DCOLL_ITEM, IP.ORDER_NO, IP.RANGE_MIN_VALN AS RANGE_MIN, IP.RANGE_MAX_VALN AS RANGE_MAX, IP.CREATR_SEQ, IP.CREATE_TMSTP, IP.UPDATER_SEQ, IP.UPDATE_TMSTP, IP.INPUT_TYPE, IP.MU_VALN AS MU, IP.SIGMA_VALN AS SIGMA, IP.LOWER_SPEC, IP.UPPER_SPEC, IP.INPUT_GROUP_NO AS INPUT_GROUP, IP.PARAM_OPTION, IP.SENSOR_OPTION_CONT " \
            "FROM IVM_SM_TMP_INPUT_PARAM IP " \
            "WHERE IP.TMP_SEQ =:tmp_seq " \
            "ORDER BY IP.INPUT_GROUP_NO, IP.ORDER_NO "
    cursor.execute(query, tmp_seq=tmp_seq)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_line_name_by_tmp_seq(cursor, result_cursor, tmp_seq):
    query = ("SELECT DISTINCT L.LINE_NAME "
             "  FROM IVM_SPACE_MODEL_TMP T "
             "  JOIN IVM_MG_MAPPING MM ON T.MODEL_GROUP_SEQ= MM.MODEL_GROUP_SEQ "
             "  JOIN IVM_MODEL M ON MM.MODEL_SEQ= M.MODEL_SEQ "
             "  JOIN IVM_LINE L ON M.LINE_ID = L.LINE_ID "
             " WHERE T.TMP_SEQ =:tmp_seq ")
    cursor.execute(query, tmp_seq=tmp_seq)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_kpi_dash_item_sf_x_dcoll_list(cursor, result_cursor):
    query = (" SELECT /* spaceuiifservice-get_isf_x_dcoll_list-2025-02-21-hanyong.eom */ "
             "        DISTINCT DECODE(RSLT.SENSOR_TYPE, 'IM', '2', '1') AS KPI_CATG_TYPE, "
             "        MST.DEVICE_ID, RSLT.STEP_SEQ AS PROC_STEP_SEQ,"
             "        '-' AS METRO_STEP_SEQ, RSLT.DCOL_ITEM_NAME AS ITEM_NAME, "
             "        DECODE(RSLT.SENSOR_TYPE, 'IM', 'ISF_X_DCOLL_IM_SENSOR', 'ISF_X_DCOLL') AS ITEM_TYPE "
             " FROM ( "
             "     SELECT M.STEP_SEQ, DC.DCOL_ITEM_NAME, T.SENSOR_TYPE "
             "      FROM ISF_MODEL M "
             "      JOIN ISF_TEMPLT_ST T ON M.MODEL_SEQ = T.MODEL_SEQ " 
             "      JOIN ISF_TEMPLT_ST_ALGRTH TA ON T.TEMPLT_ST_SEQ = TA.TEMPLT_ST_SEQ "
             "      JOIN ISF_TEMPLT_AS_DCOL_CONFIG DC ON TA.TEMPLT_ST_ALGRTH_SEQ = DC.TEMPLT_ST_ALGRTH_SEQ "
             "     WHERE 1=1 "
             "       AND DC.DCOL_YN = 'Y' "
             "     UNION "
             "     SELECT M.STEP_SEQ, DC.DCOL_ITEM_NAME, T.SENSOR_TYPE "
             "      FROM ISF_MODEL M " 
             "      JOIN ISF_TEMPLT_ST T ON M.MODEL_SEQ = T.MODEL_SEQ "
             "      JOIN ISF_TEMPLT_ST_ALGRTH TA ON T.TEMPLT_ST_SEQ = TA.TEMPLT_ST_SEQ "
             "      JOIN ISF_TEMPLT_AS_DCOL_CONFIG_SUB DC ON TA.TEMPLT_ST_ALGRTH_SEQ = DC.TEMPLT_ST_ALGRTH_SEQ "
             "     WHERE 1=1 "
             "       AND DC.DCOL_YN = 'Y' "
             "     UNION "
             "     SELECT M.STEP_SEQ, DC.DCOL_ITEM_NAME, T.SENSOR_TYPE "
             "      FROM ISF_MODEL M " 
             "      JOIN ISF_TEMPLT_PC T ON M.MODEL_SEQ = T.MODEL_SEQ "
             "      JOIN ISF_TEMPLT_PC_DCOL_CONFIG DC ON T.TEMPLT_POST_CALC_SEQ = DC.TEMPLT_POST_CALC_SEQ "
             "     WHERE 1=1 "
             "       AND DC.DCOL_YN = 'Y' "
             "     UNION "
             "     SELECT M.STEP_SEQ, DC.DCOL_ITEM_NAME, T.SENSOR_TYPE "
             "      FROM ISF_MODEL M "
             "      JOIN ISF_TEMPLT_PC T ON M.MODEL_SEQ = T.MODEL_SEQ "
             "      JOIN ISF_TEMPLT_PC_DC_SUB DC ON T.TEMPLT_POST_CALC_SEQ = DC.TEMPLT_POST_CALC_SEQ " 
             "     WHERE 1=1 "
             "       AND DC.DCOL_YN = 'Y' "
             " ) RSLT "
             " JOIN IVM_KPI_DASH_MST_INFO MST ON RSLT.STEP_SEQ = MST.PROC_STEP_SEQ "  
             " WHERE 1=1 "
             " AND RSLT.DCOL_ITEM_NAME IS NOT NULL ")
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_kpi_dash_item_vm_x_dcoll_list(cursor, result_cursor):
    query = (" SELECT /* spaceuiifservice-get_ivm_x_dcoll_list-2025-02-21-hanyong.eom */ " 
             "     DISTINCT '1' AS KPI_CATG_TYPE, MST.DEVICE_ID, MST.PROC_STEP_SEQ, "
             "     '-' AS METRO_STEP_SEQ, DCS.DCOL_ITEM_NAME AS ITEM_NAME, "
             "     'IVM_X_DCOLL' AS ITEM_TYPE "
             " FROM IVM_MODEL M "
             " JOIN IVM_DCOL_CONFIG_SENSOR DCS ON M.MODEL_SEQ = DCS.MODEL_SEQ "
             " JOIN IVM_KPI_DASH_MST_INFO MST ON M.PROC_STEP_SEQ = MST.PROC_STEP_SEQ "
             " WHERE 1=1 "
             " AND M.ALGRTH_TYPE !='SPACE' "
             " AND DCS.DCOL_ITEM_NAME IS NOT NULL "
             " AND DCS.DCOL_YN = 'Y' ")
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_kpi_dash_item_vm_y_dcoll_list(cursor, result_cursor):
    query = (" SELECT /* spaceuiifservice-get_ivm_y_dcoll_list-2025-02-21-hanyong.eom */ " 
             "        DISTINCT '2' AS KPI_CATG_TYPE, MST.DEVICE_ID, MST.PROC_STEP_SEQ, "
             "        MS.PROC_STEP_SEQ AS METRO_STEP_SEQ, DC.DCOL_ITEM_NAME AS ITEM_NAME, "
             "        'IVM_Y_DCOLL' AS ITEM_TYPE "
             "   FROM IVM_MODEL M "
             "   JOIN IVM_MODEL_STEP_PROC MS ON M.MODEL_SEQ = MS.MODEL_SEQ "
             "   JOIN IVM_DCOL_CONFIG DC ON M.MODEL_SEQ = DC.MODEL_SEQ "
             "   JOIN IVM_KPI_DASH_MST_INFO MST ON M.PROC_STEP_SEQ = MST.PROC_STEP_SEQ "
             "  WHERE 1=1 "
             "    AND M.ALGRTH_TYPE !='SPACE' "
             "    AND MS.STEP_TYPE = 'METRO_STEP' "
             "    AND DC.DCOL_ITEM_NAME IS NOT NULL "
             "    AND DC.DCOL_YN = 'Y' ")
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_kpi_dash_item_space_script_model_list(cursor, result_cursor):
    query = (" SELECT /* spaceuiifservice-get_kpi_dash_item_space_script_model_list-2025-02-21-hanyong.eom */ " 
             "        DISTINCT DECODE(TI.RNR_YN, 'Y', '2', '1') AS KPI_CATG_TYPE, MST.DEVICE_ID, MST.PROC_STEP_SEQ, "
             "        MS.PROC_STEP_SEQ AS METRO_STEP_SEQ, DC.DCOL_ITEM_NAME AS ITEM_NAME, " 
             "        DECODE(TI.RNR_YN, 'Y', 'SPACE_X_Y_DCOLL_SCRIPT_MODEL_RNR_Y', 'SPACE_X_Y_DCOLL_SCRIPT_MODEL_RNR_N') AS ITEM_TYPE  "
             "   FROM IVM_MODEL M "
             "   JOIN IVM_MG_MAPPING MM ON M.MODEL_SEQ = MM.MODEL_SEQ " 
             "   JOIN IVM_MG MG ON MM.MODEL_GROUP_SEQ = MG.MODEL_GROUP_SEQ " 
             "   JOIN IVM_MODEL_STEP_PROC MS ON M.MODEL_SEQ = MS.MODEL_SEQ " 
             "   JOIN IVM_SPACE_MODEL_TMP T ON MG.MODEL_GROUP_SEQ = T.MODEL_GROUP_SEQ "
             "   JOIN IVM_SPACE_MODEL_TMP_INFO TI ON T.TMP_SEQ = TI.TMP_SEQ "
             "   JOIN IVM_SPACE_MODEL_TMP_FILE_INFO FI ON T.TMP_SEQ = FI.TMP_SEQ "
             "   JOIN IVM_DCOL_CONFIG DC ON M.MODEL_SEQ = DC.MODEL_SEQ "
             "   JOIN IVM_KPI_DASH_MST_INFO MST ON M.PROC_STEP_SEQ = MST.PROC_STEP_SEQ "
             "  WHERE 1=1 "
             "    AND M.ALGRTH_TYPE = 'SPACE' "
             "    AND MS.STEP_TYPE = 'METRO_STEP' "
             "    AND T.MODEL_STATE = '001' "
             "    AND FI.MODEL_CODE IN ('5', '6', '7', '8') "
             "    AND DC.DCOL_ITEM_NAME IS NOT NULL "
             "    AND DC.DCOL_YN = 'Y' "
             " UNION "
             " SELECT DISTINCT DECODE(TI.RNR_YN, 'Y', '2', '1') AS KPI_CATG_TYPE, MST.DEVICE_ID, MST.PROC_STEP_SEQ, " 
             "        MS.PROC_STEP_SEQ AS METRO_STEP_SEQ, DCS.DCOL_ITEM_NAME AS ITEM_NAME, " 
             "        DECODE(TI.RNR_YN, 'Y', 'SPACE_X_Y_DCOLL_SCRIPT_MODEL_RNR_Y', 'SPACE_X_Y_DCOLL_SCRIPT_MODEL_RNR_N') AS ITEM_TYPE  "
             "   FROM IVM_MODEL M "
             "   JOIN IVM_MG_MAPPING MM ON M.MODEL_SEQ = MM.MODEL_SEQ " 
             "   JOIN IVM_MG MG ON MM.MODEL_GROUP_SEQ = MG.MODEL_GROUP_SEQ "
             "   JOIN IVM_MODEL_STEP_PROC MS ON M.MODEL_SEQ = MS.MODEL_SEQ "
             "   JOIN IVM_SPACE_MODEL_TMP T ON MG.MODEL_GROUP_SEQ = T.MODEL_GROUP_SEQ "
             "   JOIN IVM_SPACE_MODEL_TMP_INFO TI ON T.TMP_SEQ = TI.TMP_SEQ "
             "   JOIN IVM_SPACE_MODEL_TMP_FILE_INFO FI ON T.TMP_SEQ = FI.TMP_SEQ "
             "   JOIN IVM_DCOL_CONFIG_SENSOR DCS ON M.MODEL_SEQ = DCS.MODEL_SEQ "
             "   JOIN IVM_KPI_DASH_MST_INFO MST ON M.PROC_STEP_SEQ = MST.PROC_STEP_SEQ "
             "  WHERE 1=1 "
             "    AND M.ALGRTH_TYPE = 'SPACE' "
             "    AND MS.STEP_TYPE = 'METRO_STEP' "
             "    AND T.MODEL_STATE = '001' "
             "    AND FI.MODEL_CODE IN ('5', '6', '7', '8') "
             "    AND DCS.DCOL_ITEM_NAME IS NOT NULL"
             "    AND DC.DCOL_YN = 'Y' ")
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_kpi_dash_item_space_learning_model_list(cursor, result_cursor):
    query = (" SELECT /* spaceuiifservice-get_kpi_dash_item_space_learning_model_list-2025-02-21-hanyong.eom */ " 
             "        DISTINCT '2' AS KPI_CATG_TYPE, MST.DEVICE_ID, MST.PROC_STEP_SEQ, "
             "        MS.PROC_STEP_SEQ AS METRO_STEP_SEQ, DC.DCOL_ITEM_NAME AS ITEM_NAME, " 
             "        'SPACE_X_Y_DCOLL_LEARNING_MODEL' AS ITEM_TYPE "
             "   FROM IVM_MODEL M "
             "   JOIN IVM_MG_MAPPING MM ON M.MODEL_SEQ = MM.MODEL_SEQ " 
             "   JOIN IVM_MG MG ON MM.MODEL_GROUP_SEQ = MG.MODEL_GROUP_SEQ " 
             "   JOIN IVM_MODEL_STEP_PROC MS ON M.MODEL_SEQ = MS.MODEL_SEQ " 
             "   JOIN IVM_SPACE_MODEL_TMP T ON MG.MODEL_GROUP_SEQ = T.MODEL_GROUP_SEQ "
             "   JOIN IVM_SPACE_MODEL_TMP_FILE_INFO FI ON T.TMP_SEQ = FI.TMP_SEQ "
             "   JOIN IVM_DCOL_CONFIG DC ON M.MODEL_SEQ = DC.MODEL_SEQ "
             "   JOIN IVM_KPI_DASH_MST_INFO MST ON M.PROC_STEP_SEQ = MST.PROC_STEP_SEQ "
             "  WHERE 1=1 "
             "    AND M.ALGRTH_TYPE = 'SPACE' "
             "    AND MS.STEP_TYPE = 'METRO_STEP' "
             "    AND T.MODEL_STATE = '001' "
             "    AND FI.MODEL_CODE NOT IN ('5', '6', '7', '8') "
             "    AND DC.DCOL_ITEM_NAME IS NOT NULL "
             "    AND DC.DCOL_YN = 'Y' "
             " UNION "
             " SELECT DISTINCT '2' AS KPI_CATG_TYPE, MST.DEVICE_ID, MST.PROC_STEP_SEQ, " 
             "        MS.PROC_STEP_SEQ AS METRO_STEP_SEQ, DCS.DCOL_ITEM_NAME AS ITEM_NAME, " 
             "        'SPACE_X_Y_DCOLL_LEARNING_MODEL' AS ITEM_TYPE "
             "   FROM IVM_MODEL M "
             "   JOIN IVM_MG_MAPPING MM ON M.MODEL_SEQ = MM.MODEL_SEQ " 
             "   JOIN IVM_MG MG ON MM.MODEL_GROUP_SEQ = MG.MODEL_GROUP_SEQ "
             "   JOIN IVM_MODEL_STEP_PROC MS ON M.MODEL_SEQ = MS.MODEL_SEQ "
             "   JOIN IVM_SPACE_MODEL_TMP T ON MG.MODEL_GROUP_SEQ = T.MODEL_GROUP_SEQ "
             "   JOIN IVM_SPACE_MODEL_TMP_FILE_INFO FI ON T.TMP_SEQ = FI.TMP_SEQ "
             "   JOIN IVM_DCOL_CONFIG_SENSOR DCS ON M.MODEL_SEQ = DCS.MODEL_SEQ "
             "   JOIN IVM_KPI_DASH_MST_INFO MST ON M.PROC_STEP_SEQ = MST.PROC_STEP_SEQ "
             "  WHERE 1=1 "
             "    AND M.ALGRTH_TYPE = 'SPACE' "
             "    AND MS.STEP_TYPE = 'METRO_STEP' "
             "    AND T.MODEL_STATE = '001' "
             "    AND FI.MODEL_CODE NOT IN ('5', '6', '7', '8') "
             "    AND DCS.DCOL_ITEM_NAME IS NOT NULL "
             "    AND DC.DCOL_YN = 'Y' ")
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator3
def get_kpi_dash_mst_info(cursor, result_cursor, site):
    query = ("SELECT /* spaceuiifservice-get_kpi_dash_mst_info-2025-02-21-hanyong.eom */ "
             "  DISTINCT MP.NEW_CODE AS LINE_NAME, L.YMS_LINE_ID, MI.DR_CODE "
             "  , MI.DEVICE_ID, MI.PROC_STEP_SEQ, MI.AREA_NAME, MI.METRO_STEP_SEQ "
             "  FROM IVM_KPI_DASH_MST_INFO MI "
             "  JOIN IVM_DSM_DASH_MPG_DTL MP ON SUBSTR(MI.DEVICE_ID, 0, 2) = MP.OLD_CODE "
             "  JOIN IVM_LINE L ON L.LINE_NAME = MP.NEW_CODE "
             " WHERE 1=1 "
             " AND MP.SITE =:site "
             " AND MP.MPG_ID = 'DEVICE_ID-REPRSN_LINE_NAME' "
             " ORDER BY MI.DR_CODE ")
    cursor.execute(query, site=site)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_kpi_dash_item_info(cursor, result_cursor):
    query = ("SELECT /* spaceuiifservice-get_kpi_dash_item_info-2025-02-21-hanyong.eom */ "
             "  DISTINCT KPI_CATG_TYPE, DEVICE_ID, PROC_STEP_SEQ, METRO_STEP_SEQ, ITEM_NAME, ITEM_TYPE "
             "  FROM IVM_KPI_DASH_ITEM_INFO ")
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator3
def get_kpi_dash_goal_info(cursor, result_cursor, site):
    query = ("SELECT /* spaceuiifservice-get_kpi_dash_goal_info-2025-02-21-hanyong.eom */ "
             "  DISTINCT KPI_CATG_TYPE, DR_CODE, GOAL_VALN, OFFSET_VALN "
             "  FROM IVM_KPI_DASH_GOAL_INFO ")
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator3
def get_kpi_dash_score_result(cursor, result_cursor, site, query_date):
    query = ("SELECT /* spaceuiifservice-get_kpi_dash_score_result-2025-02-21-hanyong.eom */ "
             "  KPI_CATG_TYPE, DR_CODE, DEVICE_ID, PROC_STEP_SEQ, AREA_NAME, METRO_STEP_SEQ, ITEM_NAME, CREATE_TMSTP "
             "  FROM IVM_KPI_DASH_SCORE_RESULT "
             " WHERE 1=1 "
             "   AND QUERY_DATE BETWEEN TO_CHAR(TO_TIMESTAMP(:query_date, 'YYYY-MM-DD')-13, 'YYYY-MM-DD') AND :query_date "
             "   AND CREATE_TMSTP > TO_TIMESTAMP(:query_date, 'YYYY-MM-DD')-13 ")
    cursor.execute(query, query_date=query_date)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_yms_line_id(cursor, result_cursor, site, device_id):
    query = ("SELECT /* spaceuiifservice-get_yms_line_id-2025-02-21-hanyong.eom */ "
             "  DISTINCT L.YMS_LINE_ID "
             "  FROM IVM_DSM_DASH_MPG_DTL MP "
             "  JOIN IVM_LINE L ON L.LINE_NAME = MP.NEW_CODE "
             " WHERE 1=1 "
             "   AND MP.SITE = :site "
             "   AND MP.MPG_ID = 'DEVICE_ID-REPRSN_LINE_NAME' "
             "   AND MP.OLD_CODE = SUBSTR(:device_id, 0, 2) ")
    cursor.execute(query, site=site, device_id=device_id)
    result = fetch_data_one(cursor)
    return result

@vm_dao_decorator
def get_vm_kpi_dash_fail_bdq_param(cursor, result_cursor):
    query = ("SELECT /* spaceuiifservice-get_vm_kpi_dash_fail_param-2025-03-19-hanyong.eom */ "
             "    TABLE_NAME, YMS_LINE_ID, DEVICE_ID, STEP_SEQ_LIST, QUERY_DATE "
             "  FROM IVM_KPI_DASH_FAIL_BDQ_PARAM ")
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator
def get_kpi_dash_dsm_result(cursor, result_cursor, query_date):
    query = ("WITH /* spaceuiifservice-get_kpi_dash_dsm_result-2025-02-21-hanyong.eom */ MST_INFO AS ("
             "    SELECT MODEL_SEQ, MODEL_GROUP_SEQ, DR_CODE, DEVICE_ID, PROC_STEP_SEQ, "
             "           AREA_NAME, METRO_STEP_SEQ, MAX(MONITOR_STEP) AS MONITOR_STEP "
             "    FROM ( "
             "      SELECT DISTINCT MM.MODEL_SEQ, MM.MODEL_GROUP_SEQ, KDM.DR_CODE, M.DEVICE_ID, "
             "             M.PROC_STEP_SEQ, KDM.AREA_NAME, MS2.PROC_STEP_SEQ AS METRO_STEP_SEQ, "
             "             DECODE(MS.STEP_TYPE, 'MONITOR_STEP', MS.PROC_STEP_SEQ, NULL) AS MONITOR_STEP "
             "      FROM IVM_MODEL M "
             "      JOIN IVM_MG_MAPPING MM ON M.MODEL_SEQ = MM.MODEL_SEQ "
             "      JOIN IVM_MG MG ON MM.MODEL_GROUP_SEQ = MG.MODEL_GROUP_SEQ "
             "      JOIN IVM_MODEL_STEP_PROC MS ON M.MODEL_SEQ = MS.MODEL_SEQ "
             "      JOIN IVM_MODEL_STEP_PROC MS2 ON M.MODEL_SEQ = MS2.MODEL_SEQ "
             "      JOIN IVM_KPI_DASH_MST_INFO KDM ON M.DEVICE_ID = KDM.DEVICE_ID AND M.PROC_STEP_SEQ = KDM.PROC_STEP_SEQ "
             "      WHERE 1=1 "
             "          AND MS.STEP_TYPE IN ('METRO_STEP', 'MEASURE_STEP') "
             "    ) "
             "    GROUP BY MODEL_SEQ, MODEL_GROUP_SEQ, DR_CODE, DEVICE_ID, PROC_STEP_SEQ, AREA_NAME, METRO_STEP_SEQ "
             ") "
             "SELECT DISTINCT '3' AS KPI_CATG_TYPE, MST.DR_CODE, MST.DEVICE_ID, MST.PROC_STEP_SEQ, MST.AREA_NAME, "
             "       MST.METRO_STEP_SEQ, DC.DCOL_ITEM_NAME AS ITEM_NAME, MST.MONITOR_STEP "
             "  FROM MST_INFO MST "
             "  JOIN IVM_LOT_TRACK_CUR_METRO_HIST CH ON MST.MODEL_SEQ = CH.MODEL_SEQ AND MST.METRO_STEP_SEQ = CH.METRO_STEP_SEQ "
             "  JOIN IVM_DCOL_CONFIG DC ON MST.MODEL_SEQ = DC.MODEL_SEQ "
             " WHERE 1=1 "
             "   AND CH.CREATE_TMSTP BETWEEN TO_TIMESTAMP(:query_date, 'YYYY-MM-DD') AND TO_TIMESTAMP(:query_date, 'YYYY-MM-DD')+1 "
             "   AND CH.METRO_RESULT_CODE = 'PASS' "
             "UNION "
             "SELECT DISTINCT '3' AS KPI_CATG_TYPE, MST.DR_CODE, MST.DEVICE_ID, MST.PROC_STEP_SEQ, MST.AREA_NAME, "
             "       MST.METRO_STEP_SEQ, DC.DCOL_ITEM_NAME AS ITEM_NAME, MST.MONITOR_STEP "
             "  FROM MST_INFO MST "
             "  JOIN IVM_LOT_TRACK_NEXT_METRO_HIST NH ON MST.MODEL_SEQ = NH.MODEL_SEQ AND MST.METRO_STEP_SEQ = NH.METRO_STEP_SEQ "
             "  JOIN IVM_DCOL_CONFIG DC ON MST.MODEL_SEQ = DC.MODEL_SEQ "
             " WHERE 1=1 "
             "   AND NH.CREATE_TMSTP BETWEEN TO_TIMESTAMP(:query_date, 'YYYY-MM-DD') AND TO_TIMESTAMP(:query_date, 'YYYY-MM-DD')+1 "
             "   AND NH.METRO_RESULT_CODE = 'PASS' "
             "UNION "
             "SELECT DISTINCT '3' AS KPI_CATG_TYPE, MST.DR_CODE, MST.DEVICE_ID, MST.PROC_STEP_SEQ, MST.AREA_NAME, "
             "       MST.METRO_STEP_SEQ, DC.DCOL_ITEM_NAME AS ITEM_NAME, MST.MONITOR_STEP "
             "  FROM MST_INFO MST "
             "  JOIN IVM_PM_DSM_HISTORY PH ON MST.MODEL_GROUP_SEQ = PH.MODEL_GROUP_SEQ AND MST.METRO_STEP_SEQ = PH.METRO_STEP_SEQ "
             "  JOIN IVM_DCOL_CONFIG DC ON MST.MODEL_SEQ = DC.MODEL_SEQ "
             " WHERE 1=1"
             "   AND PH.CREATE_TMSTP BETWEEN TO_TIMESTAMP(:query_date, 'YYYY-MM-DD') AND TO_TIMESTAMP(:query_date, 'YYYY-MM-DD')+1 "
             "   AND PH.METRO_RESULT_CODE = 'PASS' ")
    cursor.execute(query, query_date=query_date)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator2
def insert_vm_kpi_dash_item_info(conn, cursor, insert_list):
    query = "INSERT INTO IVM_KPI_DASH_ITEM_INFO (KPI_CATG_TYPE, DEVICE_ID, PROC_STEP_SEQ, METRO_STEP_SEQ, ITEM_NAME, ITEM_TYPE, CREATE_TMSTP) " \
            "VALUES (:kpi_catg_type, :device_id, :proc_step_seq, :metro_step_seq, :item_name, :item_type, SYSTIMESTAMP)"
    cursor.prepare(query)
    cursor.executemany(None, insert_list)
    conn.commit()

@vm_dao_decorator
def truncate_vm_kpi_dash_item_info(conn, cursor):
    query = "TRUNCATE TABLE IVM_KPI_DASH_ITEM_INFO"
    cursor.execute(query)

@vm_dao_decorator
def truncate_vm_kpi_dash_fail_bdq_param(conn, cursor):
    query = "TRUNCATE TABLE IVM_KPI_DASH_FAIL_BDQ_PARAM"
    cursor.execute(query)

@vm_dao_decorator2
def insert_vm_kpi_dash_score_result(conn, cursor, insert_list):
    query = "INSERT INTO IVM_KPI_DASH_SCORE_RESULT (KPI_CATG_TYPE, DR_CODE, DEVICE_ID, PROC_STEP_SEQ, AREA_NAME, METRO_STEP_SEQ, ITEM_NAME, QUERY_DATE, CREATE_TMSTP) " \
            "VALUES (:kpi_catg_type, :dr_code, :device_id, :proc_step_seq, :area_name, :metro_step_seq, :item_name, :query_date, SYSTIMESTAMP)"
    cursor.prepare(query)
    cursor.executemany(None, insert_list)
    conn.commit()

@vm_dao_decorator2
def insert_vm_kpi_dash_fail_bdq_param(conn, cursor, insert_list):
    query = "INSERT INTO IVM_KPI_DASH_FAIL_BDQ_PARAM (TABLE_NAME, YMS_LINE_ID, DEVICE_ID, STEP_SEQ_LIST, QUERY_DATE) " \
            "VALUES (:table_name, :yms_line_id, :device_id, :step_seq_list, :query_date)"
    cursor.prepare(query)
    cursor.executemany(None, insert_list)
    conn.commit()

@vm_dao_decorator2
def insert_vm_mail_send(conn, cursor, input_param_dict):
    query = "Insert into IVM_MAIL_SEND (EMAIL_TITLE, EMAIL_CONT, RECVR_CONT, SENDER_ADDR, REQ_TMSTP) " \
            "Values (:email_title, :email_cont, :recvr_cont, :sender_addr, SYSTIMESTAMP) "
    cursor.execute(query, email_title=input_param_dict['EMAIL_TITLE'], email_cont=input_param_dict['EMAIL_CONT'],
                          recvr_cont=input_param_dict['RECVR_CONT'], sender_addr=input_param_dict['SENDER_ADDR'])
    conn.commit()

if __name__ == "__main__" :
    logger.info("============= vmDAO TEST  ===============")