from common.database import pt_db_conn as db_conn
from common.fetch_data import fetch_data_all, fetch_data_one
import logging
logger = logging.getLogger(__name__)
def vm_dao_decorator(func):
    def func_wrapper(*args, **kwargs):
        l_exclude_rtn = ['get_cpd_x_input_list', 'get_apc_tkout_lot_wf']
        if func.__name__ not in l_exclude_rtn:
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
        return result
    return func_wrapper
def vm_dao_decorator2(func):
    def func_wrapper(*args, **kwargs):
        l_exclude_rtn = ['ins_apc_cpd_exe_log', 'ins_ivm_apc_sp_apc_tkout_wf',
                         'del_apc_tkout_lot_wf', 'ins_ivm_apc_sp_apc_tkout_val']
        if func.__name__ not in l_exclude_rtn:
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
        return result
    return func_wrapper
@vm_dao_decorator
def get_site_info(cursor, result_cursor) :
    query = """
        SELECT /* SPACEUIIF-get_site_info-20250205-inhee.lee */
               OLD_CODE AS SITE_INFO FROM IVM_APC_SP_MST_MAPPING
         WHERE MPG_ID = 'APC_SITE_INFO' AND ROWNUM = 1
    """
    cursor.execute(query)
    result = fetch_data_one(cursor)
    return result.SITE_INFO
@vm_dao_decorator
def get_apc_batch_date(cursor, result_cursor, l_pkg_nm, l_procdr_nm) :
    query = """
        SELECT PKG_NAME ,PROCDR_NAME ,P_TYPE
              ,START_DATE ,END_DATE ,RUN_YN 
              ,SYSDATE 
              ,ROUND(((SYSDATE - END_DATE) * 24), 0) AS DIFF_HOUR
              ,(SYSDATE - 7/24) AS SYSDATE_7H
              ,(SYSDATE - 6/24) AS SYSDATE_6H
              ,(SYSDATE - 1/24) AS SYSDATE_1H
              ,(SYSDATE - 2/24) AS SYSDATE_2H
          FROM IVM_APC_SP_BATCH_TIME
         WHERE PKG_NAME = :PKG_NAME
           AND PROCDR_NAME = :PROCDR_NAME AND P_TYPE = '0'
    """
    cursor.execute(query, PKG_NAME=l_pkg_nm, PROCDR_NAME=l_procdr_nm)
    result = fetch_data_one(cursor)
    return result
@vm_dao_decorator
def get_apc_compare_date(cursor, result_cursor) :
    query = """
        SELECT MIN(FROM_DATE) AS FROM_DATE ,MAX(TO_DATE) AS TO_DATE
          FROM (
              SELECT MAX(T1.BDQ_DATE) AS FROM_DATE ,SYSDATE-60 AS TO_DATE 
                FROM IVM_APC_SP_APC_STEP T1
                WHERE T1.BDQ_DATE > SYSDATE - 7
                  AND T1.BDQ_DATE NOT IN 
                      (SELECT MAX(T1.BDQ_DATE) FROM IVM_APC_SP_APC_STEP T1
                          WHERE T1.BDQ_DATE > SYSDATE - 7)
              UNION ALL
              SELECT SYSDATE+60 AS FROM_DATE ,MAX(T1.BDQ_DATE) AS TO_DATE 
                FROM IVM_APC_SP_APC_STEP T1
                WHERE T1.BDQ_DATE > SYSDATE - 7
            )
    """
    cursor.execute(query)
    result = fetch_data_one(cursor)
    return result
@vm_dao_decorator
def get_apc_compare_date_exist_chk(cursor, result_cursor, l_fdate, l_tdate) :
    query = """
        SELECT SUM(CNT) AS CNT
          FROM (
            SELECT 1 AS CNT FROM IVM_APC_SP_APC_INFO
             WHERE BDQ_DATE = TO_DATE(:F_DATE, 'YYYYMMDD') AND ROWNUM = 1
            UNION ALL
            SELECT 1 AS CNT FROM IVM_APC_SP_APC_INFO
             WHERE BDQ_DATE = TO_DATE(:T_DATE, 'YYYYMMDD') AND ROWNUM = 1
          )
    """
    cursor.execute(query, F_DATE=l_fdate, T_DATE=l_tdate)
    result = fetch_data_one(cursor)
    return result
@vm_dao_decorator2
def upd_apc_batch_date_end(conn, cursor, l_pkg_nm, l_procdr_nm, l_sdate, l_edate) :
    query = """
        UPDATE IVM_APC_SP_BATCH_TIME
           SET START_DATE = TO_DATE(:S_DATE, 'YYYYMMDD HH24MISS')
              ,END_DATE = TO_DATE(:E_DATE, 'YYYYMMDD HH24MISS')
              ,RUN_YN = 'N'
              ,UPDATE_TMSTP = SYSTIMESTAMP
         WHERE PKG_NAME = :PKG_NAME
           AND PROCDR_NAME = :PROCDR_NAME AND P_TYPE = '0'
    """
    cursor.execute(query, S_DATE=l_sdate, E_DATE=l_edate,
                    PKG_NAME=l_pkg_nm, PROCDR_NAME=l_procdr_nm)
    conn.commit()
@vm_dao_decorator2
def upd_apc_batch_date_y(conn, cursor, l_pkg_nm, l_procdr_nm) :
    query = """
        UPDATE IVM_APC_SP_BATCH_TIME
           SET RUN_YN = 'Y'
              ,UPDATE_TMSTP = SYSTIMESTAMP
         WHERE PKG_NAME = :PKG_NAME
           AND PROCDR_NAME = :PROCDR_NAME AND P_TYPE = '0'
    """
    cursor.execute(query, PKG_NAME=l_pkg_nm, PROCDR_NAME=l_procdr_nm)
    conn.commit()
@vm_dao_decorator
def get_ivm_yms_lines(cursor, result_cursor) :
    query = """
        SELECT DISTINCT YMS_LINE_ID FROM IVM_LINE ORDER BY YMS_LINE_ID
    """
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result
@vm_dao_decorator
def get_site_db_users(cursor, result_cursor, l_site) :
    query = """
        SELECT /* SPACEUIIF-get_site_db_users-20250205-inhee.lee */
               DISTINCT OLD_CODE AS BDQ_DB_USER 
          FROM IVM_APC_SP_MST_MAPPING T
         WHERE MPG_ID = 'BDQ_DB_USER-SITE_INFO'
           AND SITE = :SITE
    """
    cursor.execute(query, SITE=l_site)
    result = fetch_data_all(cursor)
    return result
@vm_dao_decorator
def get_out_item_ids(cursor, result_cursor) :
    query = """
        SELECT DISTINCT ABMIS.ITEM_ID FROM IVM_APC_BDQ_MEAS_ITEM_SPEC ABMIS
         WHERE ABMIS.BDQ_DATE = (SELECT MAX(T1.BDQ_DATE)
                                    FROM IVM_APC_BDQ_MEAS_ITEM_SPEC T1
                                    WHERE T1.BDQ_DATE > SYSDATE - 7)
         ORDER BY ABMIS.ITEM_ID
    """
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result
@vm_dao_decorator2
def del_apc_exe_log(conn, cursor):
    query = """
        -- Execution Log Delete (Before 65 days)
        DELETE FROM IVM_APC_SP_EXE_LOG
         WHERE CREATE_TMSTP < SYSDATE - 65
    """
    cursor.execute(query)
    conn.commit()
@vm_dao_decorator2
def del_apc_sp_exe_cpd_log(conn, cursor):
    query = """
        -- Execution Log Delete (Before 65 days)
        DELETE FROM IVM_APC_SP_EXE_CPD_LOG
         WHERE CREATE_TMSTP < SYSDATE - 65
    """
    cursor.execute(query)
    conn.commit()
@vm_dao_decorator2
def ins_apc_exe_log(conn, cursor, l_bdq_date, l_msg):
    if l_bdq_date:
        query = """
            -- Execution Log Insert
            INSERT INTO IVM_APC_SP_EXE_LOG
                (DATA_FROM_TMSTP ,DATA_TO_TMSTP ,BDQ_DATE
                 ,MSG_CONT ,CREATER_SEQ ,CREATE_TMSTP)
             VALUES (SYSTIMESTAMP ,'' ,TO_DATE(:BDQ_DATE, 'YYYYMMDD')
                 ,:MSG_CONT ,-999 ,SYSTIMESTAMP)
        """
        cursor.execute(query, BDQ_DATE=l_bdq_date, MSG_CONT=l_msg)
    else:
        query = """
            -- Execution Log Insert
            INSERT INTO IVM_APC_SP_EXE_LOG
                (DATA_FROM_TMSTP ,DATA_TO_TMSTP 
                 ,MSG_CONT ,CREATER_SEQ ,CREATE_TMSTP)
             VALUES (SYSTIMESTAMP ,''
                 ,:MSG_CONT ,-999 ,SYSTIMESTAMP)
        """
        cursor.execute(query, MSG_CONT=l_msg)
    conn.commit()
@vm_dao_decorator2
def ins_apc_cpd_exe_log(conn, cursor, l_val_list):
    query = """
        -- APC CPD Execution Log Insert
        INSERT INTO IVM_APC_SP_EXE_CPD_LOG
            (PROC_STEP_SEQ ,CPD_TMSTP ,DEVICE_ID ,PPID ,ITEM_ID
             ,KS_THRESHOLD ,DATA_FROM_TMSTP ,DATA_TO_TMSTP 
             ,MSG_TYPE ,MSG_CONT ,CREATER_SEQ ,CREATE_TMSTP)
         VALUES
            (:PROC_STEP_SEQ ,TO_DATE(:CPD_TMSTP, 'YYYYMMDD HH24MISS')
             ,:DEVICE_ID ,:PPID ,:ITEM_ID ,:KS_THRESHOLD
             ,TO_DATE(:FROM_TMSTP, 'YYYYMMDD HH24MISS')
             ,TO_DATE(:TO_TMSTP, 'YYYYMMDD HH24MISS')
             ,:MSG_TYPE ,:MSG_CONT ,-999 ,SYSTIMESTAMP)
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_list)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator
def get_ivm_apc_bdq_step_mapping_chk(cursor, result_cursor, l_bdq_date):
    query = """
        SELECT 'Y' AS FLAG
          FROM IVM_APC_BDQ_STEP_MAPPING
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
           AND ROWNUM = 1
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    result = fetch_data_one(cursor)
    return result.FLAG
@vm_dao_decorator2
def del_ivm_apc_bdq_step_mapping(conn, cursor, l_date):
    query = """
        DELETE FROM IVM_APC_BDQ_STEP_MAPPING
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 8
    """
    cursor.execute(query, BDQ_DATE=l_date)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_bdq_step_mapping(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_STEP_MAPPING
            (BDQ_DATE ,BDQ_DB_USER ,PROC_STEP_SEQ ,PRE_STEP_SEQ
            ,POST_STEP_SEQ ,APC_DCOL_YN ,VM_DCOL_YN
            ,OCD_FF_YN ,OCD_FB_YN ,NEW_SEND_FDBK_YN
            ,GROUP_ID ,MGR_ID ,PHOTO_STEP ,PRE_VM_STEP
            ,PRE_VM_STEP_TYPE ,PRE_VM_ITEM_ID ,PRE_VM_GOF
            ,PRE_MEAS_OPTION ,PRE_AVG_OPTION ,APC_USE_YN ,APC_TYPE
            ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT TO_DATE(:BDQ_DATE, 'YYYYMMDD') AS BDQ_DATE, 
                :BDQ_DB_USER AS BDQ_DB_USER,
                :PROC_STEP_SEQ AS PROC_STEP_SEQ, :PRE_STEP_SEQ AS PRE_STEP_SEQ,
                :POST_STEP_SEQ AS POST_STEP_SEQ, :APC_DCOL_YN AS APC_DCOL_YN,
                :VM_DCOL_YN AS VM_DCOL_YN, :OCD_FF_YN AS OCD_FF_YN,
                :OCD_FB_YN AS OCD_FB_YN, :NEW_SEND_FDBK_YN AS NEW_SEND_FDBK_YN,
                :GROUP_ID AS GROUP_ID, :MGR_ID AS MGR_ID,
                :PHOTO_STEP AS PHOTO_STEP, :PRE_VM_STEP AS PRE_VM_STEP,
                :PRE_VM_STEP_TYPE AS PRE_VM_STEP_TYPE, :PRE_VM_ITEM_ID AS PRE_VM_ITEM_ID,
                :PRE_VM_GOF AS PRE_VM_GOF, :PRE_MEAS_OPTION AS PRE_MEAS_OPTION,
                :PRE_AVG_OPTION AS PRE_AVG_OPTION, :APC_USE_YN AS APC_USE_YN,
                :APC_TYPE AS APC_TYPE
              FROM DUAL
          )
          SELECT T0.BDQ_DATE, T0.BDQ_DB_USER, T0.PROC_STEP_SEQ,
                T0.PRE_STEP_SEQ, T0.POST_STEP_SEQ, T0.APC_DCOL_YN,
                T0.VM_DCOL_YN, T0.OCD_FF_YN, T0.OCD_FB_YN, T0.NEW_SEND_FDBK_YN,
                T0.GROUP_ID, T0.MGR_ID, T0.PHOTO_STEP, T0.PRE_VM_STEP,
                T0.PRE_VM_STEP_TYPE, T0.PRE_VM_ITEM_ID, T0.PRE_VM_GOF,
                T0.PRE_MEAS_OPTION, T0.PRE_AVG_OPTION, T0.APC_USE_YN, T0.APC_TYPE,
                -999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_bdq_fb_group(conn, cursor, l_date, l_src):
    query = """
        DELETE FROM IVM_APC_BDQ_FB_GROUP
         WHERE (BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 8)
           AND (SRC_TYPE = :SRC_TYPE OR SRC_TYPE IS NULL)
    """
    cursor.execute(query, BDQ_DATE=l_date, SRC_TYPE=l_src)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_bdq_fb_group(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_FB_GROUP
            (BDQ_DATE ,BDQ_DB_USER ,DEVICE_ID ,PROC_STEP_SEQ ,PPID ,LINE_INFO 
            ,FDBK_GROUP ,BDQ_UPDATE_TMSTP ,SRC_TYPE
            ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT TO_DATE(:BDQ_DATE, 'YYYYMMDD') AS BDQ_DATE, 
                :BDQ_DB_USER AS BDQ_DB_USER, :DEVICE_ID AS DEVICE_ID,
                :PROC_STEP_SEQ AS PROC_STEP_SEQ, :PPID AS PPID,
                :LINE_INFO AS LINE_INFO, :FDBK_GROUP AS FDBK_GROUP,
                TO_DATE(:BDQ_UPDATE_TMSTP, 'YYYYMMDD HH24MISS') AS BDQ_UPDATE_TMSTP,
                :SRC_TYPE AS SRC_TYPE
              FROM DUAL
          )
          SELECT T0.BDQ_DATE ,T0.BDQ_DB_USER ,T0.DEVICE_ID ,T0.PROC_STEP_SEQ 
                ,T0.PPID ,T0.LINE_INFO ,T0.FDBK_GROUP ,T0.BDQ_UPDATE_TMSTP 
                ,T0.SRC_TYPE ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_bdq_mimo_spec(conn, cursor, l_date, l_src):
    query = """
        DELETE FROM IVM_APC_BDQ_MIMO_SPEC
         WHERE (BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD') 
            OR BDQ_DATE < SYSDATE - 8)
           AND (SRC_TYPE = :SRC_TYPE OR SRC_TYPE IS NULL)
    """
    cursor.execute(query, BDQ_DATE=l_date, SRC_TYPE=l_src)
    conn.commit()
@vm_dao_decorator2
def del_ivm_apc_bdq_cvd_side_sys(conn, cursor, l_date, l_src):
    query = """
        DELETE FROM IVM_APC_BDQ_CVD_SIDE_SYS
         WHERE (BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD') 
            OR BDQ_DATE < SYSDATE - 8)
           AND (SRC_TYPE = :SRC_TYPE OR SRC_TYPE IS NULL)
    """
    cursor.execute(query, BDQ_DATE=l_date, SRC_TYPE=l_src)
    conn.commit()
@vm_dao_decorator2
def del_ivm_apc_bdq_cvd_side(conn, cursor, l_date, l_src):
    query = """
        DELETE FROM IVM_APC_BDQ_CVD_SIDE
         WHERE (BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD') 
            OR BDQ_DATE < SYSDATE - 8)
           AND (SRC_TYPE = :SRC_TYPE OR SRC_TYPE IS NULL)
    """
    cursor.execute(query, BDQ_DATE=l_date, SRC_TYPE=l_src)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_bdq_mimo_spec(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_MIMO_SPEC
            (BDQ_DATE ,EQP_ID ,CHAMBER_ID ,FDBK_GROUP
            ,APC_APPLY_YN ,BDQ_RECIPE_STEP_ID ,PPROG_NAME ,INPUT_LIST
            ,INPUT_MAP_TYPE
            ,OUTPUT_LIST ,CONTROL_TYPE
            ,PARAM_SET_NAME ,PARAM_GROUP_NAME ,TUNING_PARAM_NAME
            ,RECIPE_STEP_ID
            ,SRC_TYPE ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT TO_DATE(:BDQ_DATE, 'YYYYMMDD') AS BDQ_DATE, 
                :EQP_ID AS EQP_ID,
                :SUB_EQP_ID AS CHAMBER_ID, :FDBK_GROUP AS FDBK_GROUP,
                :APC_APPLY_YN AS APC_APPLY_YN, :BDQ_RECIPE_STEP_ID AS BDQ_RECIPE_STEP_ID,
                :PPROG_NAME AS PPROG_NAME, :INPUT_LIST AS INPUT_LIST,
                :INPUT_MAP_TYPE AS INPUT_MAP_TYPE, :OUTPUT_LIST AS OUTPUT_LIST,
                :CONTROL_TYPE AS CONTROL_TYPE, :PARAM_SET_NAME AS PARAM_SET_NAME,
                :PARAM_GROUP_NAME AS PARAM_GROUP_NAME, 
                :TUNING_PARAM_NAME AS TUNING_PARAM_NAME,
                :RECIPE_STEP_ID AS RECIPE_STEP_ID, :SRC_TYPE AS SRC_TYPE
              FROM DUAL
          )
          SELECT T0.BDQ_DATE ,T0.EQP_ID ,T0.CHAMBER_ID ,T0.FDBK_GROUP 
                 ,T0.APC_APPLY_YN ,T0.BDQ_RECIPE_STEP_ID ,T0.PPROG_NAME ,T0.INPUT_LIST 
                 ,T0.INPUT_MAP_TYPE ,T0.OUTPUT_LIST ,T0.CONTROL_TYPE 
                 ,T0.PARAM_SET_NAME ,T0.PARAM_GROUP_NAME ,T0.TUNING_PARAM_NAME 
                 ,T0.RECIPE_STEP_ID ,T0.SRC_TYPE ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def ins_ivm_apc_bdq_mimo_spec_cvd_spec(conn, cursor, l_bdq_ymd, l_src_type):
    query = """
        INSERT INTO IVM_APC_BDQ_MIMO_SPEC
            (BDQ_DATE ,EQP_ID ,CHAMBER_ID ,FDBK_GROUP
            ,APC_APPLY_YN ,BDQ_RECIPE_STEP_ID ,PPROG_NAME 
            ,INPUT_LIST ,TUNING_PARAM_NAME
            ,OUTPUT_LIST ,PARAM_SET_NAME ,RECIPE_STEP_ID
            ,SRC_TYPE ,CREATER_SEQ ,CREATE_TMSTP)
          SELECT BCS.BDQ_DATE ,BCS.EQP_ID ,BCS.CHAMBER_ID ,BCS.FDBK_GROUP 
              ,BCS.APC_APPLY_YN ,BCS.BDQ_RECIPE_STEP_ID  ,BCS.PPROG_NAME
              ,'TIME1@TIME2' AS INPUT_LIST ,'TIME' AS TUNING_PARAM_NAME 
              ,BCSS.OUTPUT_LIST ,BCS.PARAM_SET_NAME ,BCS.RECIPE_STEP_ID
              ,:SRC_TYPE AS SRC_TYPE ,-999 ,SYSTIMESTAMP 
            FROM IVM_APC_BDQ_CVD_SIDE BCS
              LEFT OUTER JOIN IVM_APC_BDQ_CVD_SIDE_SYS BCSS
                ON BCSS.BDQ_DATE = BCS.BDQ_DATE
                  AND BCSS.FDBK_GROUP = BCS.FDBK_GROUP
                  AND BCSS.EQP_ID = BCS.EQP_ID
                  AND BCSS.CHAMBER_ID = BCS.CHAMBER_ID
                  AND BCSS.OUTPUT_LIST != '-'
            WHERE BCS.BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
    """
    cursor.execute(query, SRC_TYPE=l_src_type, BDQ_DATE=l_bdq_ymd)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def ins_ivm_apc_bdq_cvd_side_sys(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_CVD_SIDE_SYS
            (BDQ_DATE ,FDBK_GROUP ,EQP_ID ,CHAMBER_ID
            ,OUTPUT_LIST ,SRC_TYPE ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT TO_DATE(:BDQ_DATE, 'YYYYMMDD') AS BDQ_DATE, 
                :FDBK_GROUP AS FDBK_GROUP, :EQP_ID AS EQP_ID,
                :CHAMBER_ID AS CHAMBER_ID, :OUTPUT_LIST AS OUTPUT_LIST,
                :SRC_TYPE AS SRC_TYPE
              FROM DUAL
          )
          SELECT T0.BDQ_DATE ,T0.FDBK_GROUP ,T0.EQP_ID ,T0.CHAMBER_ID ,T0.OUTPUT_LIST 
                 ,T0.SRC_TYPE ,-999 ,SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def ins_ivm_apc_bdq_cvd_side(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_CVD_SIDE
            (BDQ_DATE ,FDBK_GROUP ,EQP_ID ,CHAMBER_ID ,APC_APPLY_YN
            ,PARAM_SET_NAME ,BDQ_RECIPE_STEP_ID ,RECIPE_STEP_ID 
            ,PPROG_NAME ,SRC_TYPE  ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT TO_DATE(:BDQ_DATE, 'YYYYMMDD') AS BDQ_DATE, 
                :FDBK_GROUP AS FDBK_GROUP, :EQP_ID AS EQP_ID,
                :CHAMBER_ID AS CHAMBER_ID, :APC_APPLY_YN AS APC_APPLY_YN,
                :PARAM_SET_NAME AS PARAM_SET_NAME, :BDQ_RECIPE_STEP_ID AS BDQ_RECIPE_STEP_ID,
                :RECIPE_STEP_ID AS RECIPE_STEP_ID,
                :PPROG_NAME AS PPROG_NAME, :SRC_TYPE AS SRC_TYPE
              FROM DUAL
          )
          SELECT T0.BDQ_DATE ,T0.FDBK_GROUP ,T0.EQP_ID ,T0.CHAMBER_ID ,T0.APC_APPLY_YN 
                 ,T0.PARAM_SET_NAME ,T0.BDQ_RECIPE_STEP_ID ,T0.RECIPE_STEP_ID
                 ,T0.PPROG_NAME ,T0.SRC_TYPE ,-999 ,SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_bdq_meas_item_spec(conn, cursor, l_date, l_src):
    query = """
        DELETE FROM IVM_APC_BDQ_MEAS_ITEM_SPEC
         WHERE (BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 8)
           AND (SRC_TYPE = :SRC_TYPE OR SRC_TYPE IS NULL)
    """
    cursor.execute(query, BDQ_DATE=l_date, SRC_TYPE=l_src)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_bdq_meas_item_spec(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_MEAS_ITEM_SPEC
            (BDQ_DATE ,BDQ_DB_USER ,AREA_NAME ,APC_MODEL_NAME 
             ,MEASURE_STEP_SEQ ,OUTPUT_NAME ,ITEM_ID ,SUB_ITEM_ID
             ,IMPALA_CREATE_TMSTP ,BDQ_UPDATE_TMSTP ,SRC_TYPE
             ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT TO_DATE(:BDQ_DATE, 'YYYYMMDD') AS BDQ_DATE, 
                :BDQ_DB_USER AS BDQ_DB_USER, :AREA_NAME AS AREA_NAME,
                :APC_MODEL_NAME AS APC_MODEL_NAME,
                :MEASURE_STEP_SEQ AS MEASURE_STEP_SEQ, :OUTPUT_NAME AS OUTPUT_NAME,
                :ITEM_ID AS ITEM_ID, :SUB_ITEM_ID AS SUB_ITEM_ID,
                TO_DATE(:IMPALA_CREATE_TMSTP, 'YYYYMMDD HH24MISS') AS IMPALA_CREATE_TMSTP,
                TO_DATE(:BDQ_UPDATE_TMSTP, 'YYYYMMDD HH24MISS') AS BDQ_UPDATE_TMSTP,
                :SRC_TYPE AS SRC_TYPE
              FROM DUAL
          )
          SELECT T0.BDQ_DATE ,T0.BDQ_DB_USER ,T0.AREA_NAME ,T0.APC_MODEL_NAME
                 ,T0.MEASURE_STEP_SEQ ,T0.OUTPUT_NAME ,T0.ITEM_ID ,T0.SUB_ITEM_ID
                 ,T0.IMPALA_CREATE_TMSTP ,T0.BDQ_UPDATE_TMSTP  ,T0.SRC_TYPE
                 ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_bdq_step_area(conn, cursor, l_date):
    query = """
        DELETE FROM IVM_APC_BDQ_STEP_AREA
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 65
    """
    cursor.execute(query, BDQ_DATE=l_date)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_bdq_step_area(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_STEP_AREA
            (BDQ_DATE ,PROC_STEP_SEQ ,DEVICE_ID ,AREA ,SUB_AREA 
             ,BDQ_LAST_UPDATE_TIME ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT TO_DATE(:BDQ_DATE, 'YYYYMMDD') AS BDQ_DATE, 
                :PROC_STEP_SEQ AS PROC_STEP_SEQ, :DEVICE_ID AS DEVICE_ID,
                :AREA AS AREA, :SUB_AREA AS SUB_AREA,
                TO_DATE(:BDQ_LAST_UPDATE_TIME, 'YYYYMMDD HH24MISS') AS BDQ_LAST_UPDATE_TIME
              FROM DUAL
          )
          SELECT T0.BDQ_DATE ,T0.PROC_STEP_SEQ ,T0.DEVICE_ID ,T0.AREA
                 ,T0.SUB_AREA ,T0.BDQ_LAST_UPDATE_TIME ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
@vm_dao_decorator2
def del_ivm_apc_bdq_fab_lot_apc(conn, cursor, l_fdate, l_tdate):
    query = """
        DELETE FROM IVM_APC_BDQ_FAB_LOT_APC
         WHERE (TKOUT_TIME >= TO_DATE(:F_DATE, 'YYYYMMDD HH24MISS') AND
                TKOUT_TIME < TO_DATE(:T_DATE, 'YYYYMMDD HH24MISS') )
            OR TKOUT_TIME < SYSDATE - 35
    """
    cursor.execute(query, F_DATE=l_fdate, T_DATE=l_tdate)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_bdq_fab_lot_apc(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_FAB_LOT_APC
            (PROC_STEP_SEQ ,TKOUT_TIME ,LOT_ID ,DEVICE_ID ,LINE_ID ,AREA_NAME 
            ,PPID ,EQP_ID ,CHAMBER_ID ,ITEM_ID ,FAB_VALN ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT :PROC_STEP_SEQ AS PROC_STEP_SEQ, 
                TO_DATE(:TKOUT_TIME, 'YYYYMMDD HH24MISS') AS TKOUT_TIME, 
                :LOT_ID AS LOT_ID, :DEVICE_ID AS DEVICE_ID,
                :LINE_ID AS LINE_ID, :AREA_NAME AS AREA_NAME, :PPID AS PPID,
                :EQP_ID AS EQP_ID, :CHAMBER_ID AS CHAMBER_ID, :ITEM_ID AS ITEM_ID,
                :FAB_VALN AS FAB_VALN
              FROM DUAL
          )
          SELECT T0.PROC_STEP_SEQ ,T0.TKOUT_TIME ,T0.LOT_ID ,T0.DEVICE_ID
                 ,T0.LINE_ID ,T0.AREA_NAME ,T0.PPID ,T0.EQP_ID
                 ,T0.CHAMBER_ID ,T0.ITEM_ID ,T0.FAB_VALN
                 ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_bdq_fab_wf_apc(conn, cursor, l_fdate, l_tdate):
    query = """
        DELETE FROM IVM_APC_BDQ_FAB_WF_APC
         WHERE (TKOUT_TIME >= TO_DATE(:F_DATE, 'YYYYMMDD HH24MISS') AND
                TKOUT_TIME < TO_DATE(:T_DATE, 'YYYYMMDD HH24MISS')) 
            OR TKOUT_TIME < SYSDATE - 35
    """
    cursor.execute(query, F_DATE=l_fdate, T_DATE=l_tdate)
    conn.commit()
@vm_dao_decorator2
def del_ivm_apc_bdq_fab_wf_met(conn, cursor, l_fdate, l_tdate):
    query = """
        DELETE FROM IVM_APC_BDQ_FAB_WF_MET
         WHERE (TKOUT_TIME >= TO_DATE(:F_DATE, 'YYYYMMDD HH24MISS') AND
                TKOUT_TIME < TO_DATE(:T_DATE, 'YYYYMMDD HH24MISS')) 
            OR TKOUT_TIME < SYSDATE - 35
    """
    cursor.execute(query, F_DATE=l_fdate, T_DATE=l_tdate)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_bdq_fab_wf_apc(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_FAB_WF_APC
            (PROC_STEP_SEQ ,TKOUT_TIME ,LOT_ID ,DEVICE_ID ,LINE_ID ,AREA_NAME 
            ,PPID ,EQP_ID ,CHAMBER_ID ,ITEM_ID ,WAFER_ID ,FAB_VALN 
            ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT :PROC_STEP_SEQ AS PROC_STEP_SEQ, 
                TO_DATE(:TKOUT_TIME, 'YYYYMMDD HH24MISS') AS TKOUT_TIME, 
                :LOT_ID AS LOT_ID, :DEVICE_ID AS DEVICE_ID,
                :LINE_ID AS LINE_ID, :AREA_NAME AS AREA_NAME, :PPID AS PPID,
                :EQP_ID AS EQP_ID, :CHAMBER_ID AS CHAMBER_ID, :ITEM_ID AS ITEM_ID,
                :WAFER_ID AS WAFER_ID, :FAB_VALN AS FAB_VALN
              FROM DUAL
          )
          SELECT T0.PROC_STEP_SEQ ,T0.TKOUT_TIME ,T0.LOT_ID ,T0.DEVICE_ID
                 ,T0.LINE_ID ,T0.AREA_NAME ,T0.PPID ,T0.EQP_ID
                 ,T0.CHAMBER_ID ,T0.ITEM_ID ,T0.WAFER_ID ,T0.FAB_VALN
                 ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount

@vm_dao_decorator2
def ins_ivm_apc_bdq_fab_wf_met(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_FAB_WF_MET
            (METRO_STEP_SEQ ,TKOUT_TIME ,LOT_ID ,DEVICE_ID ,YMS_LINE_ID ,LINE_ID 
            ,AREA_NAME ,PPID ,EQP_ID ,ITEM_ID ,SUB_ITEM_ID ,WAFER_ID ,FAB_VALN 
            ,ROOT_LOT_ID ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT :METRO_STEP_SEQ AS METRO_STEP_SEQ, 
                TO_DATE(:TKOUT_TIME, 'YYYYMMDD HH24MISS') AS TKOUT_TIME, 
                :LOT_ID AS LOT_ID, :DEVICE_ID AS DEVICE_ID,
                :YMS_LINE_ID AS YMS_LINE_ID, :LINE_ID AS LINE_ID,
                :AREA_NAME AS AREA_NAME, :PPID AS PPID, :EQP_ID AS EQP_ID,
                :ITEM_ID AS ITEM_ID, :SUB_ITEM_ID AS SUB_ITEM_ID,
                :WAFER_ID AS WAFER_ID, :FAB_VALN AS FAB_VALN,
                :ROOT_LOT_ID AS ROOT_LOT_ID
              FROM DUAL
          )
          SELECT T0.METRO_STEP_SEQ ,T0.TKOUT_TIME ,T0.LOT_ID ,T0.DEVICE_ID
                 ,T0.YMS_LINE_ID ,T0.LINE_ID ,T0.AREA_NAME ,T0.PPID ,T0.EQP_ID
                 ,T0.ITEM_ID ,T0.SUB_ITEM_ID ,T0.WAFER_ID ,T0.FAB_VALN
                 ,T0.ROOT_LOT_ID ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_sp_apc_outitem(conn, cursor, l_bdq_date):
    query = """
        DELETE FROM IVM_APC_SP_APC_OUTITEM
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 16
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_outitem(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_APC_OUTITEM
              (BDQ_DATE ,MEASURE_STEP_SEQ ,AREA_NAME ,OUTPUT_ITEM_ID
              ,CREATER_SEQ ,CREATE_TMSTP)
          SELECT BDQ_DATE ,MEASURE_STEP_SEQ  ,AREA_NAME
                ,LISTAGG(ITEM_ID, '|') WITHIN GROUP(ORDER BY ITEM_ID) AS ITEM_IDS
                ,-999 ,SYSTIMESTAMP
          FROM (
            SELECT DISTINCT BDQ_DATE ,MEASURE_STEP_SEQ ,ITEM_ID ,AREA_NAME
              FROM IVM_APC_BDQ_MEAS_ITEM_SPEC
             WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
             ORDER BY MEASURE_STEP_SEQ ,ITEM_ID) T0
          GROUP BY BDQ_DATE ,MEASURE_STEP_SEQ ,AREA_NAME
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_sp_apc_info(conn, cursor, l_bdq_date):
    query = """
        DELETE FROM IVM_APC_SP_APC_INFO
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 16
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_info(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_APC_INFO
              (BDQ_DATE ,PROC_STEP_SEQ ,PRE_STEP_SEQ ,POST_STEP_SEQ ,DEVICE_ID 
              ,LINE_INFO ,PPID ,FDBK_GROUP ,RECIPE_STEP_ID ,TUNING_PARAM_NAME
              ,INPUT_MAP_TYPE ,PARAM_SET_NAME ,FB_OUTPUT_ITEM_ID ,FF_OUTPUT_ITEM_ID
              ,CREATER_SEQ ,CREATE_TMSTP)
          SELECT T_ROW.BDQ_DATE ,T_ROW.PROC_STEP_SEQ ,T_ROW.PRE_STEP_SEQ 
                ,T_ROW.POST_STEP_SEQ ,T_ROW.DEVICE_ID ,T_ROW.LINE_INFO
                ,T_ROW.PPID ,T_ROW.FDBK_GROUP 
                ,T_ROW.RECIPE_STEP_ID ,T_ROW.TUNING_PARAM_NAME 
                ,T_ROW.INPUT_MAP_TYPE ,T_ROW.PARAM_SET_NAME
                ,T_ROW.FB_OUTPUT_ITEM_ID ,T_ROW.FF_OUTPUT_ITEM_ID
                ,-999 ,SYSTIMESTAMP
            FROM (
              SELECT DISTINCT SM.BDQ_DATE ,SM.PROC_STEP_SEQ ,SM.PRE_STEP_SEQ 
                    ,SM.POST_STEP_SEQ ,BFG.DEVICE_ID --,BFG.LINE_INFO 
                    ,NVL(MPG.NEW_CODE, 'N/A') AS LINE_INFO ,BFG.PPID 
                    ,BFG.FDBK_GROUP ,MS.RECIPE_STEP_ID ,MS.TUNING_PARAM_NAME 
                    ,MS.INPUT_MAP_TYPE ,MS.PARAM_SET_NAME 
                    ,FB_SAO.OUTPUT_ITEM_ID AS FB_OUTPUT_ITEM_ID
                    ,FF_SAO.OUTPUT_ITEM_ID AS FF_OUTPUT_ITEM_ID
                    ,MS.FDBK_GROUP AS MS_CHK 
                    ,NVL(FB_SAO.MEASURE_STEP_SEQ, FF_SAO.MEASURE_STEP_SEQ) AS OUT_CHK
                FROM IVM_APC_BDQ_STEP_MAPPING SM
                  JOIN IVM_APC_BDQ_FB_GROUP BFG
                    ON BFG.BDQ_DATE = SM.BDQ_DATE
                      AND BFG.PROC_STEP_SEQ = SM.PROC_STEP_SEQ
                      AND BFG.BDQ_DB_USER = SM.BDQ_DB_USER
                  LEFT OUTER JOIN IVM_APC_SP_MST_MAPPING MPG
                    ON MPG.OLD_CODE = SM.BDQ_DB_USER
                      AND MPG.MPG_ID = 'BDQ_DB_USER-LINE_INFO'
                      AND BFG.BDQ_DB_USER = SM.BDQ_DB_USER
                  LEFT OUTER JOIN IVM_APC_BDQ_MIMO_SPEC MS
                    ON MS.BDQ_DATE = BFG.BDQ_DATE
                      AND MS.FDBK_GROUP = BFG.FDBK_GROUP
                      AND MS.APC_APPLY_YN	= 'Y'
                  LEFT OUTER JOIN IVM_APC_SP_APC_OUTITEM FB_SAO
                    ON FB_SAO.BDQ_DATE = SM.BDQ_DATE
                      AND FB_SAO.MEASURE_STEP_SEQ = SM.POST_STEP_SEQ
                  LEFT OUTER JOIN IVM_APC_SP_APC_OUTITEM FF_SAO
                    ON FF_SAO.BDQ_DATE = SM.BDQ_DATE
                      AND FF_SAO.MEASURE_STEP_SEQ = SM.PRE_STEP_SEQ
                WHERE 1=1
                  --AND SM.APC_DCOL_YN = 'Y'
                  AND SM.BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            )   T_ROW
            WHERE T_ROW.MS_CHK IS NOT NULL
              AND T_ROW.OUT_CHK IS NOT NULL
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_sp_apc_step(conn, cursor, l_bdq_date):
    query = """
        DELETE FROM IVM_APC_SP_APC_STEP
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 16
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_step(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_APC_STEP
              (BDQ_DATE ,PROC_STEP_SEQ ,PRE_STEP_SEQ ,POST_STEP_SEQ
              ,DEVICE_ID ,LINE_INFO ,APC_DCOL_YN ,APC_TYPE ,AREA_NAME
              ,CREATER_SEQ ,CREATE_TMSTP)
          SELECT DISTINCT T_ROW.BDQ_DATE ,T_ROW.PROC_STEP_SEQ ,T_ROW.PRE_STEP_SEQ 
                ,T_ROW.POST_STEP_SEQ ,T_ROW.DEVICE_ID ,T_ROW.LINE_INFO
                ,T_ROW.APC_DCOL_YN ,T_ROW.APC_TYPE ,T_ROW.AREA_NAME
                ,-999 ,SYSTIMESTAMP
            FROM (
              SELECT DISTINCT SM.BDQ_DATE ,SM.PROC_STEP_SEQ ,SM.PRE_STEP_SEQ 
                    ,SM.POST_STEP_SEQ ,BFG.DEVICE_ID  --,BFG.LINE_INFO 
                    ,NVL(MPG.NEW_CODE, 'N/A') AS LINE_INFO
                    ,SUBSTR(SM.APC_DCOL_YN,1,1) AS APC_DCOL_YN ,SM.APC_TYPE
                    ,NVL(SASA.AREA_NAME, 'N/A') AS AREA_NAME
                    ,MS.FDBK_GROUP AS MS_CHK 
                    ,NVL(FB_SAO.MEASURE_STEP_SEQ, FF_SAO.MEASURE_STEP_SEQ) AS OUT_CHK
                FROM IVM_APC_BDQ_STEP_MAPPING SM
                  JOIN IVM_APC_BDQ_FB_GROUP BFG
                    ON BFG.BDQ_DATE = SM.BDQ_DATE
                      AND BFG.PROC_STEP_SEQ = SM.PROC_STEP_SEQ
                      AND BFG.BDQ_DB_USER = SM.BDQ_DB_USER
                  LEFT OUTER JOIN IVM_APC_SP_MST_MAPPING MPG
                    ON MPG.OLD_CODE = SM.BDQ_DB_USER
                      AND MPG.MPG_ID = 'BDQ_DB_USER-LINE_INFO'
                  LEFT OUTER JOIN IVM_APC_BDQ_MIMO_SPEC MS
                    ON MS.BDQ_DATE = BFG.BDQ_DATE
                      AND MS.FDBK_GROUP = BFG.FDBK_GROUP
                      AND MS.APC_APPLY_YN = 'Y'
                  LEFT OUTER JOIN IVM_APC_SP_APC_OUTITEM FB_SAO
                    ON FB_SAO.BDQ_DATE = SM.BDQ_DATE
                      AND FB_SAO.MEASURE_STEP_SEQ  = SM.POST_STEP_SEQ
                  LEFT OUTER JOIN IVM_APC_SP_APC_OUTITEM FF_SAO
                    ON FF_SAO.BDQ_DATE = SM.BDQ_DATE
                      AND FF_SAO.MEASURE_STEP_SEQ  = SM.PRE_STEP_SEQ
                  LEFT OUTER JOIN IVM_APC_SP_APC_STEP_AREA SASA
                    ON SASA.PROC_STEP_SEQ = SM.PROC_STEP_SEQ
                      AND SASA.DEVICE_ID = BFG.DEVICE_ID
                WHERE 1=1
                  --AND SM.APC_DCOL_YN = 'Y'
                  AND SM.BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            )   T_ROW
            WHERE T_ROW.MS_CHK IS NOT NULL
              AND T_ROW.OUT_CHK IS NOT NULL
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_sp_apc_in_fb(conn, cursor, l_bdq_date):
    query = """
        DELETE FROM IVM_APC_SP_MST_IN_FB
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 16
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_in_fb(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_MST_IN_FB
              (BDQ_DATE ,FDBK_GROUP ,APC_APPLY_YN ,RECIPE_STEP_ID
              ,TUNING_PARAM_NAME)
          SELECT DISTINCT MS.BDQ_DATE ,MS.FDBK_GROUP ,MS.APC_APPLY_YN 
                ,MS.RECIPE_STEP_ID ,MS.TUNING_PARAM_NAME
            FROM IVM_APC_BDQ_MIMO_SPEC MS
          WHERE NOT EXISTS
                  (SELECT 1 FROM IVM_APC_SP_MST_IN_FB SMIF
                    WHERE SMIF.BDQ_DATE = MS.BDQ_DATE
                      AND SMIF.FDBK_GROUP = MS.FDBK_GROUP
                      AND SMIF.APC_APPLY_YN = MS.APC_APPLY_YN
                      AND SMIF.RECIPE_STEP_ID = MS.RECIPE_STEP_ID
                      AND SMIF.TUNING_PARAM_NAME = MS.TUNING_PARAM_NAME)
            AND MS.BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_in_param(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_MST_IN_PARAM
              (TUNING_PARAM_NAME, CREATER_SEQ, CREATE_TMSTP)
          SELECT DISTINCT MS.TUNING_PARAM_NAME ,-999 ,SYSTIMESTAMP
            FROM IVM_APC_BDQ_MIMO_SPEC MS
           WHERE NOT EXISTS
                  (SELECT 1 FROM IVM_APC_SP_MST_IN_PARAM SIPR
                    WHERE SIPR.TUNING_PARAM_NAME = MS.TUNING_PARAM_NAME)
            AND MS.BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator
def sel_ivm_apc_sp_apc_in_param(cursor, result_cursor):
    query = """
        SELECT TUNING_PARAM_NAME FROM IVM_APC_SP_MST_IN_PARAM
         WHERE RULE_TYPE IS NULL
    """
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result
@vm_dao_decorator
def sel_ivm_apc_sp_mst_mapping(cursor, result_cursor):
    query = """
        SELECT OLD_CODE ,NEW_CODE FROM IVM_APC_SP_MST_MAPPING
         WHERE MPG_ID = 'IN_PARAM-IN_PARAM_TYPE'
         ORDER BY OLD_ORDER_NO
    """
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_in_param_row(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_SP_MST_IN_PARAM
            (TUNING_PARAM_NAME ,RULE_TYPE ,INPUT_PARAM_NAME 
            ,INPUT_PARAM_CNT ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT 
                :TUNING_PARAM_NAME AS TUNING_PARAM_NAME, 
                :RULE_TYPE AS RULE_TYPE,
                :INPUT_PARAM_NAME AS INPUT_PARAM_NAME,
                :INPUT_PARAM_CNT AS INPUT_PARAM_CNT
              FROM DUAL
          )
          SELECT T0.TUNING_PARAM_NAME ,T0.RULE_TYPE 
                ,T0.INPUT_PARAM_NAME ,T0.INPUT_PARAM_CNT
                ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def upd_ivm_apc_sp_apc_in_param_all(conn, cursor, l_name, l_all_param, l_cnt):
    query = """
        UPDATE IVM_APC_SP_MST_IN_PARAM
           SET RULE_TYPE = 'ALL'
              ,INPUT_PARAM_NAME = :INPUT_PARAM_NAME
              ,INPUT_PARAM_CNT = :CNT
              ,UPDATER_SEQ = -999
              ,UPDATE_TMSTP = SYSTIMESTAMP
         WHERE TUNING_PARAM_NAME = :PARAM_NAME
           AND RULE_TYPE IS NULL
    """
    cursor.execute(query, PARAM_NAME=l_name, INPUT_PARAM_NAME=l_all_param, CNT=l_cnt)
    conn.commit()
@vm_dao_decorator2
def del_ivm_apc_sp_apc_x_val_wf(conn, cursor, l_fdate, l_tdate):
    query = """
        DELETE FROM IVM_APC_SP_APC_X_VAL
         WHERE ((TKOUT_TIME >= TO_DATE(:F_TIME, 'YYYYMMDD HH24MISS') AND
                TKOUT_TIME < TO_DATE(:T_TIME, 'YYYYMMDD HH24MISS')) OR
                TKOUT_TIME < SYSDATE - 35)
           AND WAFER_ID <> '*'
    """
    cursor.execute(query, F_TIME=l_fdate, T_TIME=l_tdate)
    conn.commit()
@vm_dao_decorator
def sel_isf_event_hist(cursor, result_cursor, l_fdate, l_tdate):
    query = """
        SELECT DISTINCT SUBSTR(EVENT_CONT, 0, INSTR(EVENT_CONT, ' ')-1) AS EVENT_CONT
              ,EVENT_OCCUR_TMSTP ,LINE_ID ,DEVICE_ID ,EQP_ID ,STEP_SEQ ,PPID ,LOT_ID
              ,CASE WHEN INSTR(LOT_ID, '.') = 0 THEN LOT_ID 
                    ELSE SUBSTR(LOT_ID, 1, INSTR(LOT_ID, '.') - 1)
               END AS ROOT_LOT_ID
          FROM (
            SELECT SUBSTR(EVENT_CONT, INSTR(EVENT_CONT, 'WF_VISIT_HISTORY=')+17) AS EVENT_CONT
                  ,CAST(EVENT_OCCUR_TMSTP AS DATE) AS EVENT_OCCUR_TMSTP
                  ,LINE_ID ,DEVICE_ID ,EQP_ID ,STEP_SEQ ,PPID ,LOT_ID
              FROM ISF_EVENT_HIST HIST
              WHERE EVENT_OCCUR_TMSTP >= TO_DATE(:F_DATE, 'YYYYMMDD HH24MISS')
                AND EVENT_OCCUR_TMSTP < TO_DATE(:T_DATE, 'YYYYMMDD HH24MISS')
                AND EVENT_ORIGIN_CODE = 'TRACKING'
                AND EVENT_CONT LIKE '%WF_VISIT_HISTORY%'
                AND STEP_SEQ <> '-' AND DEVICE_ID LIKE '____'
            ) TMP_WF
          WHERE EXISTS (SELECT 1 FROM IVM_APC_SP_APC_STEP_AREA SASA
                         WHERE SASA.PROC_STEP_SEQ = TMP_WF.STEP_SEQ)
    """
    cursor.execute(query, F_DATE=l_fdate, T_DATE=l_tdate)
    result = fetch_data_all(cursor)
    return result
@vm_dao_decorator2
def del_ivm_apc_sp_apc_tkout_lot(conn, cursor, l_fdate, l_tdate):
    query = """
        DELETE FROM IVM_APC_SP_APC_TKOUT_LOT
         WHERE ((EVENT_OCCUR_TMSTP >= TO_DATE(:F_TIME, 'YYYYMMDD HH24MISS') AND
                EVENT_OCCUR_TMSTP < TO_DATE(:T_TIME, 'YYYYMMDD HH24MISS'))
            OR  EVENT_OCCUR_TMSTP < SYSDATE - 35)
    """
    cursor.execute(query, F_TIME=l_fdate, T_TIME=l_tdate)
    conn.commit()
@vm_dao_decorator2
def del_ivm_apc_sp_apc_tkout_wf(conn, cursor, l_fdate, l_tdate):
    query = """
        DELETE FROM IVM_APC_SP_APC_TKOUT_WF
         WHERE (ROOT_LOT_ID, STEP_SEQ, EVENT_OCCUR_TMSTP) IN
                (SELECT ROOT_LOT_ID, STEP_SEQ, EVENT_OCCUR_TMSTP 
                  FROM IVM_APC_SP_APC_TKOUT_LOT
                 WHERE ((EVENT_OCCUR_TMSTP >= TO_DATE(:F_TIME, 'YYYYMMDD HH24MISS') AND
                         EVENT_OCCUR_TMSTP < TO_DATE(:T_TIME, 'YYYYMMDD HH24MISS'))
                    OR  EVENT_OCCUR_TMSTP < SYSDATE - 35)
                )
    """
    cursor.execute(query, F_TIME=l_fdate, T_TIME=l_tdate)
    conn.commit()
@vm_dao_decorator
def sel_metro_tkout_lot_list(cursor, result_cursor, l_fdate, l_tdate):
    query = """
        WITH TMP_METRO_ROW AS (
          -- Y TREND (Y TREND) Select
          SELECT DISTINCT BFWM.METRO_STEP_SEQ ,BFWM.LOT_ID ,BFWM.TKOUT_TIME
                ,BFWM.ROOT_LOT_ID 
            FROM IVM_APC_BDQ_FAB_WF_MET BFWM
          WHERE BFWM.TKOUT_TIME >= TO_DATE(:F_DATE, 'YYYYMMDD HH24MISS')
            AND BFWM.TKOUT_TIME < TO_DATE(:T_DATE, 'YYYYMMDD HH24MISS')
            --AND TKOUT_TIME  > sysdate - 12/24
            --AND BFWM.METRO_STEP_SEQ = 'VT185250'
            --and BFWM.LOT_ID = 'B5S046.1'
        )
        , TMP_PROC_STEP_ROW AS (
          -- PROC_STEP + METRO_STEP Select
          SELECT DISTINCT POST_STEP_SEQ AS METRO_STEP_SEQ ,PROC_STEP_SEQ
            FROM IVM_APC_SP_APC_STEP
            WHERE BDQ_DATE > SYSDATE - 5 AND POST_STEP_SEQ IS NOT NULL
          UNION 
          SELECT DISTINCT PRE_STEP_SEQ AS METRO_STEP_SEQ ,PROC_STEP_SEQ
            FROM IVM_APC_SP_APC_STEP
            WHERE BDQ_DATE > SYSDATE - 5 AND PRE_STEP_SEQ IS NOT NULL
        )
        , TMP_PROC_ADD_ROW AS (
          -- METRO_STEP -> PROC_STEP Join
          SELECT TMR.METRO_STEP_SEQ ,TMR.LOT_ID ,TMR.TKOUT_TIME ,TMR.ROOT_LOT_ID
                ,TPSR.PROC_STEP_SEQ
            FROM TMP_METRO_ROW TMR
              LEFT OUTER JOIN TMP_PROC_STEP_ROW TPSR
                ON TPSR.METRO_STEP_SEQ = TMR.METRO_STEP_SEQ
            WHERE TPSR.PROC_STEP_SEQ IS NOT NULL
        )
        , TMP_TKOUT_ROW AS (
          -- METRO + TKOUT Match Join
          SELECT TPAR.METRO_STEP_SEQ ,TPAR.LOT_ID ,TPAR.TKOUT_TIME ,TPAR.ROOT_LOT_ID
                ,TPAR.PROC_STEP_SEQ  ,SATL.EVENT_OCCUR_TMSTP
                ,ROW_NUMBER() OVER(PARTITION BY TPAR.METRO_STEP_SEQ ,TPAR.LOT_ID 
                        ,TPAR.TKOUT_TIME ,TPAR.ROOT_LOT_ID ,TPAR.PROC_STEP_SEQ
                        ORDER BY SATL.EVENT_OCCUR_TMSTP DESC) AS RN
            FROM TMP_PROC_ADD_ROW TPAR
              LEFT OUTER JOIN IVM_APC_SP_APC_TKOUT_LOT SATL
                ON SATL.ROOT_LOT_ID = TPAR.ROOT_LOT_ID
                  AND SATL.STEP_SEQ = TPAR.PROC_STEP_SEQ
                  AND SATL.EVENT_OCCUR_TMSTP <= TPAR.TKOUT_TIME
                  AND SATL.EVENT_OCCUR_TMSTP > SYSDATE - 16
            WHERE SATL.EVENT_OCCUR_TMSTP IS NOT NULL
        )
        -- METRO Vs TKOUT(MAX) List Select
        SELECT TTR.METRO_STEP_SEQ ,TTR.LOT_ID ,TTR.TKOUT_TIME ,TTR.ROOT_LOT_ID
              ,TTR.PROC_STEP_SEQ ,TTR.EVENT_OCCUR_TMSTP AS MAX_EVENT_OCCUR_TMSTP
          FROM TMP_TKOUT_ROW TTR
          WHERE RN = 1
    """
    cursor.execute(query, F_DATE=l_fdate, T_DATE=l_tdate)
    result = fetch_data_all(cursor)
    return result

@vm_dao_decorator2
def ins_ivm_apc_bdq_fab_wf_met(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_BDQ_FAB_WF_MET
            (METRO_STEP_SEQ ,TKOUT_TIME ,LOT_ID ,DEVICE_ID ,YMS_LINE_ID ,LINE_ID 
            ,AREA_NAME ,PPID ,EQP_ID ,ITEM_ID ,SUB_ITEM_ID ,WAFER_ID ,FAB_VALN 
            ,ROOT_LOT_ID ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT :METRO_STEP_SEQ AS METRO_STEP_SEQ, 
                TO_DATE(:TKOUT_TIME, 'YYYYMMDD HH24MISS') AS TKOUT_TIME, 
                :LOT_ID AS LOT_ID, :DEVICE_ID AS DEVICE_ID,
                :YMS_LINE_ID AS YMS_LINE_ID, :LINE_ID AS LINE_ID,
                :AREA_NAME AS AREA_NAME, :PPID AS PPID, :EQP_ID AS EQP_ID,
                :ITEM_ID AS ITEM_ID, :SUB_ITEM_ID AS SUB_ITEM_ID,
                :WAFER_ID AS WAFER_ID, :FAB_VALN AS FAB_VALN,
                :ROOT_LOT_ID AS ROOT_LOT_ID
              FROM DUAL
          )
          SELECT T0.METRO_STEP_SEQ ,T0.TKOUT_TIME ,T0.LOT_ID ,T0.DEVICE_ID
                 ,T0.YMS_LINE_ID ,T0.LINE_ID ,T0.AREA_NAME ,T0.PPID ,T0.EQP_ID
                 ,T0.ITEM_ID ,T0.SUB_ITEM_ID ,T0.WAFER_ID ,T0.FAB_VALN
                 ,T0.ROOT_LOT_ID ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_sp_apc_outitem(conn, cursor, l_bdq_date):
    query = """
        DELETE FROM IVM_APC_SP_APC_OUTITEM
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 16
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_outitem(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_APC_OUTITEM
              (BDQ_DATE ,MEASURE_STEP_SEQ ,AREA_NAME ,OUTPUT_ITEM_ID
              ,CREATER_SEQ ,CREATE_TMSTP)
          SELECT BDQ_DATE ,MEASURE_STEP_SEQ  ,AREA_NAME
                ,LISTAGG(ITEM_ID, '|') WITHIN GROUP(ORDER BY ITEM_ID) AS ITEM_IDS
                ,-999 ,SYSTIMESTAMP
          FROM (
            SELECT DISTINCT BDQ_DATE ,MEASURE_STEP_SEQ ,ITEM_ID ,AREA_NAME
              FROM IVM_APC_BDQ_MEAS_ITEM_SPEC
             WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
             ORDER BY MEASURE_STEP_SEQ ,ITEM_ID) T0
          GROUP BY BDQ_DATE ,MEASURE_STEP_SEQ ,AREA_NAME
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_sp_apc_info(conn, cursor, l_bdq_date):
    query = """
        DELETE FROM IVM_APC_SP_APC_INFO
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 16
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_info(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_APC_INFO
              (BDQ_DATE ,PROC_STEP_SEQ ,PRE_STEP_SEQ ,POST_STEP_SEQ ,DEVICE_ID 
              ,LINE_INFO ,PPID ,FDBK_GROUP ,RECIPE_STEP_ID ,TUNING_PARAM_NAME
              ,INPUT_MAP_TYPE ,PARAM_SET_NAME ,FB_OUTPUT_ITEM_ID ,FF_OUTPUT_ITEM_ID
              ,CREATER_SEQ ,CREATE_TMSTP)
          SELECT T_ROW.BDQ_DATE ,T_ROW.PROC_STEP_SEQ ,T_ROW.PRE_STEP_SEQ 
                ,T_ROW.POST_STEP_SEQ ,T_ROW.DEVICE_ID ,T_ROW.LINE_INFO
                ,T_ROW.PPID ,T_ROW.FDBK_GROUP 
                ,T_ROW.RECIPE_STEP_ID ,T_ROW.TUNING_PARAM_NAME 
                ,T_ROW.INPUT_MAP_TYPE ,T_ROW.PARAM_SET_NAME
                ,T_ROW.FB_OUTPUT_ITEM_ID ,T_ROW.FF_OUTPUT_ITEM_ID
                ,-999 ,SYSTIMESTAMP
            FROM (
              SELECT DISTINCT SM.BDQ_DATE ,SM.PROC_STEP_SEQ ,SM.PRE_STEP_SEQ 
                    ,SM.POST_STEP_SEQ ,BFG.DEVICE_ID --,BFG.LINE_INFO 
                    ,NVL(MPG.NEW_CODE, 'N/A') AS LINE_INFO ,BFG.PPID 
                    ,BFG.FDBK_GROUP ,MS.RECIPE_STEP_ID ,MS.TUNING_PARAM_NAME 
                    ,MS.INPUT_MAP_TYPE ,MS.PARAM_SET_NAME 
                    ,FB_SAO.OUTPUT_ITEM_ID AS FB_OUTPUT_ITEM_ID
                    ,FF_SAO.OUTPUT_ITEM_ID AS FF_OUTPUT_ITEM_ID
                    ,MS.FDBK_GROUP AS MS_CHK 
                    ,NVL(FB_SAO.MEASURE_STEP_SEQ, FF_SAO.MEASURE_STEP_SEQ) AS OUT_CHK
                FROM IVM_APC_BDQ_STEP_MAPPING SM
                  JOIN IVM_APC_BDQ_FB_GROUP BFG
                    ON BFG.BDQ_DATE = SM.BDQ_DATE
                      AND BFG.PROC_STEP_SEQ = SM.PROC_STEP_SEQ
                      AND BFG.BDQ_DB_USER = SM.BDQ_DB_USER
                  LEFT OUTER JOIN IVM_APC_SP_MST_MAPPING MPG
                    ON MPG.OLD_CODE = SM.BDQ_DB_USER
                      AND MPG.MPG_ID = 'BDQ_DB_USER-LINE_INFO'
                      AND BFG.BDQ_DB_USER = SM.BDQ_DB_USER
                  LEFT OUTER JOIN IVM_APC_BDQ_MIMO_SPEC MS
                    ON MS.BDQ_DATE = BFG.BDQ_DATE
                      AND MS.FDBK_GROUP = BFG.FDBK_GROUP
                      AND MS.APC_APPLY_YN	= 'Y'
                  LEFT OUTER JOIN IVM_APC_SP_APC_OUTITEM FB_SAO
                    ON FB_SAO.BDQ_DATE = SM.BDQ_DATE
                      AND FB_SAO.MEASURE_STEP_SEQ = SM.POST_STEP_SEQ
                  LEFT OUTER JOIN IVM_APC_SP_APC_OUTITEM FF_SAO
                    ON FF_SAO.BDQ_DATE = SM.BDQ_DATE
                      AND FF_SAO.MEASURE_STEP_SEQ = SM.PRE_STEP_SEQ
                WHERE 1=1
                  --AND SM.APC_DCOL_YN = 'Y'
                  AND SM.BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            )   T_ROW
            WHERE T_ROW.MS_CHK IS NOT NULL
              AND T_ROW.OUT_CHK IS NOT NULL
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_sp_apc_step(conn, cursor, l_bdq_date):
    query = """
        DELETE FROM IVM_APC_SP_APC_STEP
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 16
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_step(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_APC_STEP
              (BDQ_DATE ,PROC_STEP_SEQ ,PRE_STEP_SEQ ,POST_STEP_SEQ
              ,DEVICE_ID ,LINE_INFO ,APC_DCOL_YN ,APC_TYPE ,AREA_NAME
              ,CREATER_SEQ ,CREATE_TMSTP)
          SELECT DISTINCT T_ROW.BDQ_DATE ,T_ROW.PROC_STEP_SEQ ,T_ROW.PRE_STEP_SEQ 
                ,T_ROW.POST_STEP_SEQ ,T_ROW.DEVICE_ID ,T_ROW.LINE_INFO
                ,T_ROW.APC_DCOL_YN ,T_ROW.APC_TYPE ,T_ROW.AREA_NAME
                ,-999 ,SYSTIMESTAMP
            FROM (
              SELECT DISTINCT SM.BDQ_DATE ,SM.PROC_STEP_SEQ ,SM.PRE_STEP_SEQ 
                    ,SM.POST_STEP_SEQ ,BFG.DEVICE_ID  --,BFG.LINE_INFO 
                    ,NVL(MPG.NEW_CODE, 'N/A') AS LINE_INFO
                    ,SUBSTR(SM.APC_DCOL_YN,1,1) AS APC_DCOL_YN ,SM.APC_TYPE
                    ,NVL(SASA.AREA_NAME, 'N/A') AS AREA_NAME
                    ,MS.FDBK_GROUP AS MS_CHK 
                    ,NVL(FB_SAO.MEASURE_STEP_SEQ, FF_SAO.MEASURE_STEP_SEQ) AS OUT_CHK
                FROM IVM_APC_BDQ_STEP_MAPPING SM
                  JOIN IVM_APC_BDQ_FB_GROUP BFG
                    ON BFG.BDQ_DATE = SM.BDQ_DATE
                      AND BFG.PROC_STEP_SEQ = SM.PROC_STEP_SEQ
                      AND BFG.BDQ_DB_USER = SM.BDQ_DB_USER
                  LEFT OUTER JOIN IVM_APC_SP_MST_MAPPING MPG
                    ON MPG.OLD_CODE = SM.BDQ_DB_USER
                      AND MPG.MPG_ID = 'BDQ_DB_USER-LINE_INFO'
                  LEFT OUTER JOIN IVM_APC_BDQ_MIMO_SPEC MS
                    ON MS.BDQ_DATE = BFG.BDQ_DATE
                      AND MS.FDBK_GROUP = BFG.FDBK_GROUP
                      AND MS.APC_APPLY_YN = 'Y'
                  LEFT OUTER JOIN IVM_APC_SP_APC_OUTITEM FB_SAO
                    ON FB_SAO.BDQ_DATE = SM.BDQ_DATE
                      AND FB_SAO.MEASURE_STEP_SEQ  = SM.POST_STEP_SEQ
                  LEFT OUTER JOIN IVM_APC_SP_APC_OUTITEM FF_SAO
                    ON FF_SAO.BDQ_DATE = SM.BDQ_DATE
                      AND FF_SAO.MEASURE_STEP_SEQ  = SM.PRE_STEP_SEQ
                  LEFT OUTER JOIN IVM_APC_SP_APC_STEP_AREA SASA
                    ON SASA.PROC_STEP_SEQ = SM.PROC_STEP_SEQ
                      AND SASA.DEVICE_ID = BFG.DEVICE_ID
                WHERE 1=1
                  --AND SM.APC_DCOL_YN = 'Y'
                  AND SM.BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            )   T_ROW
            WHERE T_ROW.MS_CHK IS NOT NULL
              AND T_ROW.OUT_CHK IS NOT NULL
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def del_ivm_apc_sp_apc_in_fb(conn, cursor, l_bdq_date):
    query = """
        DELETE FROM IVM_APC_SP_MST_IN_FB
         WHERE BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
            OR BDQ_DATE < SYSDATE - 16
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_in_fb(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_MST_IN_FB
              (BDQ_DATE ,FDBK_GROUP ,APC_APPLY_YN ,RECIPE_STEP_ID
              ,TUNING_PARAM_NAME)
          SELECT DISTINCT MS.BDQ_DATE ,MS.FDBK_GROUP ,MS.APC_APPLY_YN 
                ,MS.RECIPE_STEP_ID ,MS.TUNING_PARAM_NAME
            FROM IVM_APC_BDQ_MIMO_SPEC MS
          WHERE NOT EXISTS
                  (SELECT 1 FROM IVM_APC_SP_MST_IN_FB SMIF
                    WHERE SMIF.BDQ_DATE = MS.BDQ_DATE
                      AND SMIF.FDBK_GROUP = MS.FDBK_GROUP
                      AND SMIF.APC_APPLY_YN = MS.APC_APPLY_YN
                      AND SMIF.RECIPE_STEP_ID = MS.RECIPE_STEP_ID
                      AND SMIF.TUNING_PARAM_NAME = MS.TUNING_PARAM_NAME)
            AND MS.BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_in_param(conn, cursor, l_bdq_date):
    query = """
        INSERT INTO IVM_APC_SP_MST_IN_PARAM
              (TUNING_PARAM_NAME, CREATER_SEQ, CREATE_TMSTP)
          SELECT DISTINCT MS.TUNING_PARAM_NAME ,-999 ,SYSTIMESTAMP
            FROM IVM_APC_BDQ_MIMO_SPEC MS
           WHERE NOT EXISTS
                  (SELECT 1 FROM IVM_APC_SP_MST_IN_PARAM SIPR
                    WHERE SIPR.TUNING_PARAM_NAME = MS.TUNING_PARAM_NAME)
            AND MS.BDQ_DATE = TO_DATE(:BDQ_DATE, 'YYYYMMDD')
    """
    cursor.execute(query, BDQ_DATE=l_bdq_date)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator
def sel_ivm_apc_sp_apc_in_param(cursor, result_cursor):
    query = """
        SELECT TUNING_PARAM_NAME FROM IVM_APC_SP_MST_IN_PARAM
         WHERE RULE_TYPE IS NULL
    """
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result
@vm_dao_decorator
def sel_ivm_apc_sp_mst_mapping(cursor, result_cursor):
    query = """
        SELECT OLD_CODE ,NEW_CODE FROM IVM_APC_SP_MST_MAPPING
         WHERE MPG_ID = 'IN_PARAM-IN_PARAM_TYPE'
         ORDER BY OLD_ORDER_NO
    """
    cursor.execute(query)
    result = fetch_data_all(cursor)
    return result
@vm_dao_decorator2
def ins_ivm_apc_sp_apc_in_param_row(conn, cursor, l_val_lists):
    query = """
        INSERT INTO IVM_APC_SP_MST_IN_PARAM
            (TUNING_PARAM_NAME ,RULE_TYPE ,INPUT_PARAM_NAME 
            ,INPUT_PARAM_CNT ,CREATER_SEQ ,CREATE_TMSTP)
          WITH TMP_ROW AS (
            SELECT 
                :TUNING_PARAM_NAME AS TUNING_PARAM_NAME, 
                :RULE_TYPE AS RULE_TYPE,
                :INPUT_PARAM_NAME AS INPUT_PARAM_NAME,
                :INPUT_PARAM_CNT AS INPUT_PARAM_CNT
              FROM DUAL
          )
          SELECT T0.TUNING_PARAM_NAME ,T0.RULE_TYPE 
                ,T0.INPUT_PARAM_NAME ,T0.INPUT_PARAM_CNT
                ,-999, SYSTIMESTAMP
            FROM TMP_ROW T0
    """
    cursor.prepare(query)
    cursor.executemany(None, l_val_lists)
    conn.commit()
    return cursor.rowcount
@vm_dao_decorator2
def upd_ivm_apc_sp_apc_in_param_all(conn, cursor, l_name, l_all_param, l_cnt):
    query = """
        UPDATE IVM_APC_SP_MST_IN_PARAM
           SET RULE_TYPE = 'ALL'
              ,INPUT_PARAM_NAME = :INPUT_PARAM_NAME
              ,INPUT_PARAM_CNT = :CNT
              ,UPDATER_SEQ = -999
              ,UPDATE_TMSTP = SYSTIMESTAMP
         WHERE TUNING_PARAM_NAME = :PARAM_NAME
           AND RULE_TYPE IS NULL
    """
    cursor.execute(query, PARAM_NAME=l_name, INPUT_PARAM_NAME=l_all_param, CNT=l_cnt)
    conn.commit()
@vm_dao_decorator2
def del_ivm_apc_sp_apc_x_val_wf(conn, cursor, l_fdate, l_tdate):
    query = """
        DELETE FROM IVM_APC_SP_APC_X_VAL
         WHERE ((TKOUT_TIME >= TO_DATE(:F_TIME, 'YYYYMMDD HH24MISS') AND
                TKOUT_TIME < TO_DATE(:T_TIME, 'YYYYMMDD HH24MISS')) OR
                TKOUT_TIME < SYSDATE - 35)
           AND WAFER_ID <> '*'
    """
    cursor.execute(query, F_TIME=l_fdate, T_TIME=l_tdate)
    conn.commit()
@vm_dao_decorator
def sel_isf_event_hist(cursor, result_cursor, l_fdate, l_tdate):
    query = """
        SELECT DISTINCT SUBSTR(EVENT_CONT, 0, INSTR(EVENT_CONT, ' ')-1) AS EVENT_CONT
              ,EVENT_OCCUR_TMSTP ,LINE_ID ,DEVICE_ID ,EQP_ID ,STEP_SEQ ,PPID ,LOT_ID
              ,CASE WHEN INSTR(LOT_ID, '.') = 0 THEN LOT_ID 
                    ELSE SUBSTR(LOT_ID, 1, INSTR(LOT_ID, '.') - 1)
               END AS ROOT_LOT_ID
          FROM (
            SELECT SUBSTR(EVENT_CONT, INSTR(EVENT_CONT, 'WF_VISIT_HISTORY=')+17) AS EVENT_CONT
                  ,CAST(EVENT_OCCUR_TMSTP AS DATE) AS EVENT_OCCUR_TMSTP
                  ,LINE_ID ,DEVICE_ID ,EQP_ID ,STEP_SEQ ,PPID ,LOT_ID
              FROM ISF_EVENT_HIST HIST
              WHERE EVENT_OCCUR_TMSTP >= TO_DATE(:F_DATE, 'YYYYMMDD HH24MISS')
                AND EVENT_OCCUR_TMSTP < TO_DATE(:T_DATE, 'YYYYMMDD HH24MISS')
                AND EVENT_ORIGIN_CODE = 'TRACKING'
                AND EVENT_CONT LIKE '%WF_VISIT_HISTORY%'
                AND STEP_SEQ <> '-' AND DEVICE_ID LIKE '____'
            ) TMP_WF
          WHERE EXISTS (SELECT 1 FROM IVM_APC_SP_APC_STEP_AREA SASA
                         WHERE SASA.PROC_STEP_SEQ = TMP_WF.STEP_SEQ)
    """
    cursor.execute(query, F_DATE=l_fdate, T_DATE=l_tdate)
    result = fetch_data_all(cursor)
    return result
@vm_dao_decorator2
def del_ivm_apc_sp_apc_tkout_lot(conn, cursor, l_fdate, l_tdate):
    query = """
        DELETE FROM IVM_APC_SP_APC_TKOUT_LOT
         WHERE ((EVENT_OCCUR_TMSTP >= TO_DATE(:F_TIME, 'YYYYMMDD HH24MISS') AND
                EVENT_OCCUR_TMSTP < TO_DATE(:T_TIME, 'YYYYMMDD HH24MISS'))
            OR  EVENT_OCCUR_TMSTP < SYSDATE - 35)
    """
    cursor.execute(query, F_TIME=l_fdate, T_TIME=l_tdate)
    conn.commit()
@vm_dao_decorator2
def del_ivm_apc_sp_apc_tkout_wf(conn, cursor, l_fdate, l_tdate):
    query = """
        DELETE FROM IVM_APC_SP_APC_TKOUT_WF
         WHERE (ROOT_LOT_ID, STEP_SEQ, EVENT_OCCUR_TMSTP) IN
                (SELECT ROOT_LOT_ID, STEP_SEQ, EVENT_OCCUR_TMSTP 
                  FROM IVM_APC_SP_APC_TKOUT_LOT
                 WHERE ((EVENT_OCCUR_TMSTP >= TO_DATE(:F_TIME, 'YYYYMMDD HH24MISS') AND
                         EVENT_OCCUR_TMSTP < TO_DATE(:T_TIME, 'YYYYMMDD HH24MISS'))
                    OR  EVENT_OCCUR_TMSTP < SYSDATE - 35)
                )
    """
    cursor.execute(query, F_TIME=l_fdate, T_TIME=l_tdate)
    conn.commit()
@vm_dao_decorator
def sel_metro_tkout_lot_list(cursor, result_cursor, l_fdate, l_tdate):
    query = """
        WITH TMP_METRO_ROW AS (
          -- Y TREND (Y TREND) Select
          SELECT DISTINCT BFWM.METRO_STEP_SEQ ,BFWM.LOT_ID ,BFWM.TKOUT_TIME
                ,BFWM.ROOT_LOT_ID 
            FROM IVM_APC_BDQ_FAB_WF_MET BFWM
          WHERE BFWM.TKOUT_TIME >= TO_DATE(:F_DATE, 'YYYYMMDD HH24MISS')
            AND BFWM.TKOUT_TIME < TO_DATE(:T_DATE, 'YYYYMMDD HH24MISS')
            --AND TKOUT_TIME  > sysdate - 12/24
            --AND BFWM.METRO_STEP_SEQ = 'VT185250'
            --and BFWM.LOT_ID = 'B5S046.1'
        )
        , TMP_PROC_STEP_ROW AS (
          -- PROC_STEP + METRO_STEP Select
          SELECT DISTINCT POST_STEP_SEQ AS METRO_STEP_SEQ ,PROC_STEP_SEQ
            FROM IVM_APC_SP_APC_STEP
            WHERE BDQ_DATE > SYSDATE - 5 AND POST_STEP_SEQ IS NOT NULL
          UNION 
          SELECT DISTINCT PRE_STEP_SEQ AS METRO_STEP_SEQ ,PROC_STEP_SEQ
            FROM IVM_APC_SP_APC_STEP
            WHERE BDQ_DATE > SYSDATE - 5 AND PRE_STEP_SEQ IS NOT NULL
        )
        , TMP_PROC_ADD_ROW AS (
          -- METRO_STEP -> PROC_STEP Join
          SELECT TMR.METRO_STEP_SEQ ,TMR.LOT_ID ,TMR.TKOUT_TIME ,TMR.ROOT_LOT_ID
                ,TPSR.PROC_STEP_SEQ
            FROM TMP_METRO_ROW TMR
              LEFT OUTER JOIN TMP_PROC_STEP_ROW TPSR
                ON TPSR.METRO_STEP_SEQ = TMR.METRO_STEP_SEQ
            WHERE TPSR.PROC_STEP_SEQ IS NOT NULL
        )
        , TMP_TKOUT_ROW AS (
          -- METRO + TKOUT Match Join
          SELECT TPAR.METRO_STEP_SEQ ,TPAR.LOT_ID ,TPAR.TKOUT_TIME ,TPAR.ROOT_LOT_ID
                ,TPAR.PROC_STEP_SEQ  ,SATL.EVENT_OCCUR_TMSTP
                ,ROW_NUMBER() OVER(PARTITION BY TPAR.METRO_STEP_SEQ ,TPAR.LOT_ID 
                        ,TPAR.TKOUT_TIME ,TPAR.ROOT_LOT_ID ,TPAR.PROC_STEP_SEQ
                        ORDER BY SATL.EVENT_OCCUR_TMSTP DESC) AS RN
            FROM TMP_PROC_ADD_ROW TPAR
              LEFT OUTER JOIN IVM_APC_SP_APC_TKOUT_LOT SATL
                ON SATL.ROOT_LOT_ID = TPAR.ROOT_LOT_ID
                  AND SATL.STEP_SEQ = TPAR.PROC_STEP_SEQ
                  AND SATL.EVENT_OCCUR_TMSTP <= TPAR.TKOUT_TIME
                  AND SATL.EVENT_OCCUR_TMSTP > SYSDATE - 16
            WHERE SATL.EVENT_OCCUR_TMSTP IS NOT NULL
        )
        -- METRO Vs TKOUT(MAX) List Select
        SELECT TTR.METRO_STEP_SEQ ,TTR.LOT_ID ,TTR.TKOUT_TIME ,TTR.ROOT_LOT_ID
              ,TTR.PROC_STEP_SEQ ,TTR.EVENT_OCCUR_TMSTP AS MAX_EVENT_OCCUR_TMSTP
          FROM TMP_TKOUT_ROW TTR
          WHERE RN = 1
    """
    cursor.execute(query, F_DATE=l_fdate, T_DATE=l_tdate)
    result = fetch_data_all(cursor)
    return result

