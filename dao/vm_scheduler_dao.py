from common.database import pt_db_conn as db_conn
from common.fetch_data import fetch_data_all, fetch_data_one
import logging
logger = logging.getLogger(__name__)
def vm_dao_decorator(func):
    def func_wrapper(*args, **kwargs):
        logger.info("vm_sched_dao.{0} {1}".format(func.__name__, "called."))
        conn = db_conn()
        cursor = conn.cursor()
        result_cursor = conn.cursor()
        result = None
        try:
            result = func(cursor, result_cursor, *args, **kwargs)
        except Exception as e:
            logger.error("vm_sched_dao.{0} {1} e : {2}".format(func.__name__, " unexpected exception occuered...", e))
        finally:
            cursor.close()
            result_cursor.close()
            conn.close()
        # logger.info("vm_sched_dao.{0} {1}".format(func.__name__, "completed."))
        return result
    return func_wrapper
def vm_dao_decorator2(func):
    def func_wrapper(*args, **kwargs):
        logger.info("vm_sched_dao.{0} {1}".format(func.__name__, "called."))
        conn = db_conn()
        cursor = conn.cursor()
        result = None
        try:
            result = func(conn, cursor, *args, **kwargs)
        except Exception as e:
            logger.error("vm_sched_dao.{0} {1} e : {2}".format(func.__name__, " unexpected exception occuered...", e))
        finally:
            cursor.close()
            conn.close()
        # logger.info("vm_sched_dao.{0} {1}".format(func.__name__, "completed."))
        return result
    return func_wrapper
############# SQL ############
@vm_dao_decorator
def get_spc_itl_site_info(cursor, result_cursor) :
    query = """
        SELECT /* SPACEUIIF-get_spc_itl_site_info-250307- */
               SITE FROM IVM_DSM_DASH_MPG_DTL
         WHERE MPG_ID = 'SPC_ITL_SITE_INFO'
    """
    cursor.execute(query)
    result = fetch_data_one(cursor)
    return result.SITE
# END get_site_info
@vm_dao_decorator
def get_ivm_yms_lines(cursor, result_cursor) :
    query = """
        SELECT DISTINCT YMS_LINE_ID FROM IVM_LINE ORDER BY YMS_LINE_ID
    """
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result
# END get_ivm_yms_lines
@vm_dao_decorator2
def ins_spc_itl(conn, cursor, l_val_list):
    query = """
        INSERT /* SPACEUIIF-ins_spc_itl-250307- */
          INTO IVM_DSM_DASH_SPC_ITL_ROW
            (DSM_DATE, DEVICE_ID, LINE_ID, LOT_ID, METRO_STEP_SEQ, 
             REPRSN_LINE_NAME, REPRSN_DR_CODE, CREATER_SEQ, CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT TO_DATE(:DSM_DATE, 'YYYYMMDD') AS DSM_DATE 
                  ,:LINE_ID AS LINE_ID ,:PROCESS_ID AS DEVICE_ID
                  ,:LOT_ID AS LOT_ID ,:METRO_STEP_SEQ AS METRO_STEP_SEQ
              FROM DUAL
          )
          SELECT T0.DSM_DATE ,T0.DEVICE_ID ,T0.LINE_ID ,T0.LOT_ID ,T0.METRO_STEP_SEQ
               ,NVL(LINE_MPG.NEW_CODE, SUBSTR(T0.DEVICE_ID, 1,2)) AS REP_LINE_NAME
               ,NVL(DR_MPG.NEW_CODE, T0.DEVICE_ID) AS REP_DR_CODE
               ,-999 ,SYSTIMESTAMP
           FROM TMP_ROW T0
              JOIN IVM_DSM_DASH_MPG_DTL SPC_SITE
                  ON SPC_SITE.MPG_ID = 'SPC_ITL_SITE_INFO'
              LEFT OUTER JOIN IVM_DSM_DASH_MPG_DTL DR_MPG
                  ON T0.DEVICE_ID LIKE DR_MPG.OLD_CODE
                      AND DR_MPG.SITE = SPC_SITE.SITE
                      AND DR_MPG.MPG_ID = 'DEVICE_ID-DR_CODE'
              LEFT OUTER JOIN IVM_DSM_DASH_MPG_DTL LINE_MPG
                  ON LINE_MPG.OLD_CODE = SUBSTR(T0.DEVICE_ID, 1,2)
                      AND LINE_MPG.SITE = SPC_SITE.SITE
                      AND LINE_MPG.MPG_ID = 'DEVICE_ID-REPRSN_LINE_NAME'
          WHERE NOT EXISTS (SELECT 1 FROM IVM_DSM_DASH_SPC_ITL_ROW T1
                             WHERE T1.DEVICE_ID = T0.DEVICE_ID
                               AND T1.LINE_ID = T0.LINE_ID
                               AND T1.LOT_ID = T0.LOT_ID
                               AND T1.METRO_STEP_SEQ = T0.METRO_STEP_SEQ
                               AND T1.DSM_DATE >= T0.DSM_DATE - 2)
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_list)
    conn.commit()
    return cursor.rowcount
# END ins_spc_itl
@vm_dao_decorator
def get_cpd_tatget_model(cursor, result_cursor) :
    # 특정 기간범위의 (최대30일기준) 존재 Model 현황 조회
    query = """
        WITH TMP_ROW AS (
          SELECT DISTINCT RO_ROW.TMP_SEQ ,RO_ROW.MODEL_TYPE ,RO_ROW.MODEL_GROUP_SEQ
            FROM IVM_CPD_MODEL_RM_OP_ROW RO_ROW
            WHERE WAFER_END_TMSTP >= SYSDATE-40
        )
        SELECT RO_ROW.TMP_SEQ ,RO_ROW.MODEL_TYPE ,RO_ROW.MODEL_GROUP_SEQ
              ,CPD_CFG.MODEL_CPD_YN ,CPD_CFG.KS_THRESHOLD 
              ,NVL(CPD_CFG.MIN_WAFER_CNT, 100) AS MIN_WAFER_CNT
              ,NVL(CPD_CFG.MIN_CPD_DAYS, 7) AS MIN_CPD_DAYS
              ,NVL(CPD_CFG.MAX_CPD_DAYS, 30) AS MAX_CPD_DAYS
              ,NVL(CPD_CFG.ACCUM_DAYS_YN, 'Y') AS ACCUM_DAYS_YN
              ,SYSDATE - NVL(CPD_CFG.MIN_CPD_DAYS, 7) AS MIN_CPD_DATE
              ,SYSDATE - NVL(CPD_CFG.MAX_CPD_DAYS, 30) AS MAX_CPD_DATE
              ,SYSDATE AS NOW_DATE
          FROM TMP_ROW RO_ROW
            LEFT OUTER JOIN IVM_SM_TMP_CPD_CONFIG CPD_CFG
              ON CPD_CFG.MODEL_GROUP_SEQ = RO_ROW.MODEL_GROUP_SEQ
                AND CPD_CFG.MODEL_CPD_YN = 'Y'
    """
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result
# END get_cpd_tatget_model
@vm_dao_decorator
def get_cpd_detection_date(cursor, result_cursor, l_tmp_seq, l_model_type
                , l_from_cpd_date, l_cpd_tdate) :
    # CPD 최종 발생건 확인 (시작 날짜 조회) (미존재시 조회시작일로)
    query = """
        SELECT NVL(MAX(RO_CPD.CPD_TMSTP), 
                   TO_DATE(:FROM_DATE, 'YYYYMMDD HH24MISS')) AS CPD_FROM_DATE
          FROM IVM_CPD_MODEL_RM_OP_CPD RO_CPD
          WHERE RO_CPD.TMP_SEQ = :TMP_SEQ
            AND RO_CPD.MODEL_TYPE = :MODEL_TYPE
            AND RO_CPD.CPD_TMSTP >= TO_DATE(:FROM_DATE, 'YYYYMMDD HH24MISS')
            AND RO_CPD.CPD_TMSTP <= TO_DATE(:TO_DATE, 'YYYYMMDD HH24MISS')
    """
    cursor.execute(query, TMP_SEQ=l_tmp_seq, MODEL_TYPE=l_model_type
                , FROM_DATE=l_from_cpd_date, TO_DATE=l_cpd_tdate)
    result = fetch_data_one(cursor)
    return result.CPD_FROM_DATE
# END get_cpd_detection_date
@vm_dao_decorator
def get_cpd_sensor_cnt(cursor, result_cursor, l_tmp_seq, l_model_type, l_cpd_fdate,
                l_cpd_tdate, l_min_cnt):
    # 센서의 WAFER 개수가 최소 이상 건인지 확인
    query = """
        SELECT 'Y' AS FLAG
          FROM (
            SELECT COUNT(*) AS CNT
              FROM IVM_CPD_MODEL_RM_OP_ROW RO_ROW
             WHERE RO_ROW.WAFER_END_TMSTP >= TO_DATE(:FROM_DATE, 'YYYYMMDD HH24MISS')
               AND RO_ROW.WAFER_END_TMSTP <= TO_DATE(:TO_DATE, 'YYYYMMDD HH24MISS')
               AND RO_ROW.TMP_SEQ = :TMP_SEQ
               AND RO_ROW.MODEL_TYPE = :MODEL_TYPE
             GROUP BY RO_ROW.OUTPUT_NAME
             HAVING COUNT(*) >= :MIN_WAFER_CNT
            )
         WHERE ROWNUM = 1
    """
    cursor.execute(query, TMP_SEQ=l_tmp_seq, MODEL_TYPE=l_model_type,
                        FROM_DATE=l_cpd_fdate, MIN_WAFER_CNT=l_min_cnt,
                        TO_DATE=l_cpd_tdate)
    result = fetch_data_one(cursor)
    return result.FLAG
# END get_cpd_sensor_cnt
@vm_dao_decorator
def get_cpd_sensor_list(cursor, result_cursor, l_tmp_seq, l_model_type,
            l_cpd_fdate, l_cpd_tdate):
    # 센서 목록 조회
    query = """
        SELECT DISTINCT RO_ROW.OUTPUT_NAME
          FROM IVM_CPD_MODEL_RM_OP_ROW RO_ROW
         WHERE RO_ROW.WAFER_END_TMSTP >= TO_DATE(:FROM_DATE, 'YYYYMMDD HH24MISS') 
           AND RO_ROW.WAFER_END_TMSTP <= TO_DATE(:TO_DATE, 'YYYYMMDD HH24MISS') 
           AND RO_ROW.TMP_SEQ = :TMP_SEQ
           AND RO_ROW.MODEL_TYPE = :MODEL_TYPE
         ORDER BY RO_ROW.OUTPUT_NAME
    """
    cursor.execute(query, TMP_SEQ=l_tmp_seq, MODEL_TYPE=l_model_type,
                          FROM_DATE=l_cpd_fdate, TO_DATE=l_cpd_tdate)
    result = fetch_data_all(cursor)
    return result
# END get_cpd_sensor_cnt
@vm_dao_decorator
def get_cpd_row_data(cursor, result_cursor, l_tmp_seq, l_model_type,
            l_from_cpd_date, l_to_cpd_date):
    # CPD 대상 데이터 가져오기
    query = """
        SELECT RO_ROW.TMP_SEQ ,RO_ROW.MODEL_TYPE 
              ,RO_ROW.OUTPUT_NAME ,RO_ROW.DEVIATION_VALN ,RO_ROW.WAFER_END_TMSTP 
          FROM IVM_CPD_MODEL_RM_OP_ROW RO_ROW
          WHERE 1=1
            AND RO_ROW.WAFER_END_TMSTP >= TO_DATE(:FROM_DATE, 'YYYYMMDD HH24MISS')
            AND RO_ROW.WAFER_END_TMSTP <= TO_DATE(:TO_DATE, 'YYYYMMDD HH24MISS')
            AND RO_ROW.TMP_SEQ = :TMP_SEQ
            AND RO_ROW.MODEL_TYPE = :MODEL_TYPE
          ORDER BY RO_ROW.TMP_SEQ ,RO_ROW.MODEL_TYPE ,RO_ROW.OUTPUT_NAME 
                  ,RO_ROW.WAFER_END_TMSTP 
    """
    cursor.execute(query, FROM_DATE=l_from_cpd_date, TO_DATE=l_to_cpd_date,
                        TMP_SEQ=l_tmp_seq, MODEL_TYPE=l_model_type)
    result = fetch_data_all(cursor)
    return result
# END get_cpd_row_data
@vm_dao_decorator2
def del_cpd_exe_log(conn, cursor):
    query = """
        -- Execution Log Delete (Before 100 days)
        DELETE FROM IVM_CPD_MODEL_CPD_EXE_LOG
         WHERE CREATE_TMSTP < SYSDATE - 100
    """
    cursor.execute(query)
    conn.commit()
# END del_cpd_exe_log
@vm_dao_decorator2
def ins_cpd_exe_log_start(conn, cursor, l_tmp_seq, l_model_type,
                    l_cpd_fdate, l_cpd_tdate, l_txt):
    query = """
        -- Execution Log Insert
        INSERT INTO IVM_CPD_MODEL_CPD_EXE_LOG
            (TMP_SEQ ,MODEL_TYPE ,DATA_FROM_TMSTP ,DATA_TO_TMSTP
             ,ERR_MSG_CONT ,CREATER_SEQ ,CREATE_TMSTP)
         VALUES (:TMP_SEQ ,:MODEL_TYPE
             ,TO_DATE(:FROM_TMSTP, 'YYYYMMDD HH24MISS')
             ,TO_DATE(:TO_TMSTP, 'YYYYMMDD HH24MISS')
             ,:ERR_MSG_CONT ,-999 ,SYSTIMESTAMP)
    """
    cursor.execute(query, TMP_SEQ=l_tmp_seq, MODEL_TYPE=l_model_type,
                    FROM_TMSTP=l_cpd_fdate, TO_TMSTP=l_cpd_tdate, ERR_MSG_CONT=l_txt)
    conn.commit()
# END ins_cpd_exe_log_start
@vm_dao_decorator2
def ins_cpd_exe_log_end(conn, cursor, l_tmp_seq, l_model_type, l_ks_threshold,
                    l_cpd_tmstp, l_fdata_tmstp, l_tdata_tmstp, l_txt):
    query = """
        -- Execution Log Insert
        INSERT INTO IVM_CPD_MODEL_CPD_EXE_LOG
            (TMP_SEQ ,MODEL_TYPE ,KS_THRESHOLD ,CPD_TMSTP 
             ,DATA_FROM_TMSTP ,DATA_TO_TMSTP
             ,ERR_MSG_CONT ,CREATER_SEQ ,CREATE_TMSTP)
         VALUES (:TMP_SEQ ,:MODEL_TYPE ,:KS_THRESHOLD 
             ,TO_DATE(:CPD_TMSTP, 'YYYYMMDD HH24MISS')
             ,TO_DATE(:DATA_FROM_TMSTP, 'YYYYMMDD HH24MISS')
             ,TO_DATE(:DATA_TO_TMSTP, 'YYYYMMDD HH24MISS')
             ,:ERR_MSG_CONT ,-999 ,SYSTIMESTAMP)
    """
    cursor.execute(query, TMP_SEQ=l_tmp_seq, MODEL_TYPE=l_model_type,
                    KS_THRESHOLD=l_ks_threshold, CPD_TMSTP=l_cpd_tmstp,
                    DATA_FROM_TMSTP=l_fdata_tmstp, DATA_TO_TMSTP=l_tdata_tmstp,
                    ERR_MSG_CONT=l_txt)
    conn.commit()
# END ins_cpd_exe_log_end
@vm_dao_decorator2
def ins_cpd_date(conn, cursor, l_tmp_seq, l_model_type, l_ks_threshold,
                    l_cpd_tmstp, l_fdata_tmstp, l_tdata_tmstp):
    query = """
        -- Execution Log Insert
        INSERT INTO IVM_CPD_MODEL_RM_OP_CPD
            (TMP_SEQ ,MODEL_TYPE ,KS_THRESHOLD ,CPD_TMSTP 
             ,DATA_FROM_TMSTP ,DATA_TO_TMSTP
             ,CREATER_SEQ ,CREATE_TMSTP)
         VALUES (:TMP_SEQ ,:MODEL_TYPE ,:KS_THRESHOLD
             ,TO_DATE(:CPD_TMSTP, 'YYYYMMDD HH24MISS')
             ,TO_DATE(:DATA_FROM_TMSTP, 'YYYYMMDD HH24MISS')
             ,TO_DATE(:DATA_TO_TMSTP, 'YYYYMMDD HH24MISS')
             ,-999 ,SYSTIMESTAMP)
    """
    cursor.execute(query, TMP_SEQ=l_tmp_seq, MODEL_TYPE=l_model_type,
                    KS_THRESHOLD=l_ks_threshold, CPD_TMSTP=l_cpd_tmstp,
                    DATA_FROM_TMSTP=l_fdata_tmstp, DATA_TO_TMSTP=l_tdata_tmstp)
    conn.commit()
# END ins_cpd_date