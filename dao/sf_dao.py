from common.database import pt_db_conn
from common.database import hq_db_conn
from common.fetch_data import fetch_data_all, fetch_data_one
import logging
logger = logging.getLogger(__name__)
def sf_dao_decorator(func):
    def func_wrapper(*args, **kwargs):
        logger.debug("sf_dao.{0} {1}".format(func.__name__, "called."))
        if kwargs['db_line'] == 'P':
            conn = pt_db_conn()
        else:
            conn = hq_db_conn()
        cursor = conn.cursor()
        result = None
        try:
            result = func(cursor, *args)
        except Exception as e:
            logger.exception("sf_dao.{0} {1} e : {2}".format(func.__name__, " unexpected exception occuered...", e))
        finally:
            cursor.close()
            conn.close()
        logger.debug("sf_dao.{0} {1}".format(func.__name__, "completed."))
        return result
    return func_wrapper
def sf_dao_cud_decorator(func):
    def func_wrapper(*args, **kwargs):
        logger.debug("sf_dao.{0} {1}".format(func.__name__, "called."))
        if kwargs['db_line'] == 'P':
            conn = pt_db_conn()
        else:
            conn = hq_db_conn()
        cursor = conn.cursor()
        result = None
        try:
            result = func(cursor, conn, *args)
        except Exception as e:
            logger.exception("sf_dao.{0} {1} e : {2}".format(func.__name__, " unexpected exception occuered...", e))
        finally:
            cursor.close()
            conn.close()
        logger.debug("sf_dao.{0} {1}".format(func.__name__, "completed."))
        return result
    return func_wrapper
@sf_dao_decorator
def get_isf_templt_st_seq_and_algrth_seq(cursor, step_seq, sensor_type, recipe_step_no, sensor_name):
    query = (" SELECT M.MODEL_SEQ, TST.TEMPLT_ST_SEQ, STA.TEMPLT_ST_ALGRTH_SEQ "
             " FROM ISF_MODEL M "
             " JOIN ISF_TEMPLT_ST TST ON M.MODEL_SEQ = TST.MODEL_SEQ "
             " JOIN ISF_TEMPLT_ST_ALGRTH STA ON TST.TEMPLT_ST_SEQ = STA.TEMPLT_ST_SEQ "
             "WHERE M.STEP_SEQ= :step_seq "
             "  AND TST.SENSOR_TYPE = :sensor_type "
             "  AND ((TST.ALIAS_RSTEP IS NULL AND TST.RECIPE_STEP_ID =:recipe_step_no) OR TST.ALIAS_RSTEP =:recipe_step_no) "
             "  AND STA.ALGRTH_SENSOR_NAME =:sensor_name "
             )
    cursor.execute(query, step_seq=step_seq, sensor_type=sensor_type, recipe_step_no=recipe_step_no, sensor_name=sensor_name)
    result = fetch_data_one(cursor)
    return result.MODEL_SEQ, result.TEMPLT_ST_SEQ, result.TEMPLT_ST_ALGRTH_SEQ
@sf_dao_decorator
def get_isf_templt_st_seq_and_algrth_seq_by_model_seq(cursor, model_seq, step_seq, recipe_step_no, sensor_name):
    query = (" SELECT M.MODEL_SEQ, TST.TEMPLT_ST_SEQ, STA.TEMPLT_ST_ALGRTH_SEQ "
             " FROM ISF_MODEL M "
             " JOIN ISF_TEMPLT_ST TST ON M.MODEL_SEQ = TST.MODEL_SEQ "
             " JOIN ISF_TEMPLT_ST_ALGRTH STA ON TST.TEMPLT_ST_SEQ = STA.TEMPLT_ST_SEQ "
             "WHERE M.MODEL_SEQ = :model_seq "
             "  AND M.STEP_SEQ= :step_seq "
             "  AND ((TST.ALIAS_RSTEP IS NULL AND TST.RECIPE_STEP_ID =:recipe_step_no) OR TST.ALIAS_RSTEP =:recipe_step_no) "
             "  AND STA.ALGRTH_SENSOR_NAME =:sensor_name "
             )
    cursor.execute(query, model_seq=model_seq, step_seq=step_seq, recipe_step_no=recipe_step_no, sensor_name=sensor_name)
    result = fetch_data_all(cursor)
    if result is None or len(result) == 0:
        return None, None, None
    else:
        return result[0].MODEL_SEQ, result[0].TEMPLT_ST_SEQ, result[0].TEMPLT_ST_ALGRTH_SEQ
@sf_dao_decorator
def get_isf_templt_post_calc_seq(cursor, step_seq, sensor_type, recipe_step_no, sensor_name):
    query = (" SELECT M.MODEL_SEQ, TPC.TEMPLT_POST_CALC_SEQ "
             " FROM ISF_MODEL M "
             " JOIN ISF_TEMPLT_PC TPC ON M.MODEL_SEQ = TPC.MODEL_SEQ "
             "WHERE M.STEP_SEQ= :step_seq "
             "  AND TPC.SENSOR_TYPE = :sensor_type "
             "  AND TPC.POST_CALC_RECIPE_STEP_ID = :recipe_step_no "
             "  AND TPC.POST_CALC_SENSOR_NAME =:sensor_name "
             )
    cursor.execute(query, step_seq=step_seq, sensor_type=sensor_type, recipe_step_no=recipe_step_no, sensor_name=sensor_name)
    result = fetch_data_one(cursor)
    return result.MODEL_SEQ, result.TEMPLT_POST_CALC_SEQ
@sf_dao_decorator
def get_isf_templt_st_seq_and_algrth_seq_2d(cursor, step_seq, recipe_step_no, sensor_name):
    query = (" SELECT M.MODEL_SEQ, TST.TEMPLT_ST_SEQ, STA.TEMPLT_ST_ALGRTH_SEQ "
             " FROM ISF_MODEL M "
             " JOIN ISF_TEMPLT_ST TST ON M.MODEL_SEQ = TST.MODEL_SEQ "
             " JOIN ISF_TEMPLT_ST_SPACE SP ON TST.TEMPLT_ST_SEQ = SP.TEMPLT_ST_SEQ "
             " JOIN ISF_TEMPLT_ST_ALGRTH STA ON TST.TEMPLT_ST_SEQ = STA.TEMPLT_ST_SEQ "
             "WHERE M.STEP_SEQ= :step_seq "
             "  AND ((TST.ALIAS_RSTEP IS NULL AND TST.RECIPE_STEP_ID =:recipe_step_no) OR TST.ALIAS_RSTEP =:recipe_step_no) "
             "  AND STA.ALGRTH_SENSOR_NAME =:sensor_name "
             "  AND SP.DATA2D_SAVE_YN = 'Y' "
             )
    cursor.execute(query, step_seq=step_seq, recipe_step_no=recipe_step_no, sensor_name=sensor_name)
    result = fetch_data_one(cursor)
    return result.MODEL_SEQ, result.TEMPLT_ST_SEQ, result.TEMPLT_ST_ALGRTH_SEQ
@sf_dao_decorator
def get_org_isf_model(cursor, model_seq):
    query = (" SELECT MODEL_SEQ, MODEL_NAME, STEP_SEQ, PPID, RECIPE_ID, EQP_MODEL_NAME, MASTER_YN, PROCESS_UNIT, CUST_MODEL_OPT, DELAY_TIME, RETRY_DELAY_TIME, RETRY_COUNT "
             " FROM ISF_MODEL M "
             "WHERE M.MODEL_SEQ= :model_seq "
             )
    cursor.execute(query, model_seq=model_seq)
    result = fetch_data_one(cursor)
    return result
@sf_dao_decorator
def get_org_isf_templt_st(cursor, templt_st_seq):
    query = (" SELECT TEMPLT_ST_SEQ, MODEL_SEQ, SENSOR_TYPE, RECIPE_STEP_ID, TRANSF_SENSOR_NAME, ORIGIN_SENSOR_NAME_LIST, CUST_SENSOR_OPT_LIST, TRANSF_EQTN_CONT, REF_EQTN_CONT, MDL_INDEX_EQTN_CONT, DISTR_USE_STABLE_WIN_YN, DISTR_Y_SCALE_MINM_SIZE, "
             " DISTR_Y_SCALE_MAX_SIZE, REF_EVAL_WIN_SIZE, REF_EVAL_1ST_INDEX_YN, REF_EVAL_1ST_INDEX_1ST_VALN, REF_EVAL_1ST_INDEX_2ND_VALN, REF_EVAL_2ND_INDEX_YN, REF_EVAL_2ND_INDEX_1ST_VALN, REF_EVAL_2ND_INDEX_2ND_VALN, REF_EVAL_3RD_INDEX_YN, "
             " REF_EVAL_3RD_INDEX_1ST_VALN, REF_EVAL_3RD_INDEX_2ND_VALN, MINM_WAFER_CNT, USE_UPDATE_YN, AUTO_UPDATE_YN, CYCLE_AUTO_UPDATE_YN, REF_RESULT_CONT, GOLDEN_CHAMBER_ID, GOLDEN_STATUS, RSTEP_MGT_SEQ, TEMPLT_FLOW_TYPE, ALIAS_RSTEP, REF_OES_CAL "
             " FROM ISF_TEMPLT_ST TST "
             "WHERE TST.TEMPLT_ST_SEQ= :templt_st_seq "
             )
    cursor.execute(query, templt_st_seq=templt_st_seq)
    result = fetch_data_one(cursor)
    return result
@sf_dao_decorator
def get_org_isf_templt_st_algrth(cursor, templt_st_algrth_seq):
    query = (" SELECT TEMPLT_ST_ALGRTH_SEQ, TEMPLT_ST_SEQ, ALGRTH_SENSOR_NAME, ALGRTH_NAME, ALGRTH_EQTN_CONT, TEMPLT_ST_ALGRTH_TYPE, VC_ENABLE_YN, VC_CB_FILTER_CONT, FDC_QPASS_CONFIRM_SEQ, BATCH_TYPE_WAFER_OPT_CODE, BATCH_TYPE_WAFER_OPT_SPEC "
             " FROM ISF_TEMPLT_ST_ALGRTH STA "
             "WHERE STA.TEMPLT_ST_ALGRTH_SEQ= :templt_st_algrth_seq "
             )
    cursor.execute(query, templt_st_algrth_seq=templt_st_algrth_seq)
    result = fetch_data_one(cursor)
    return result
@sf_dao_decorator
def get_copied_isf_model_list(cursor, step_seq, ppid, recipe_id):
    query = (" SELECT MODEL_SEQ, MODEL_NAME, STEP_SEQ, PPID, RECIPE_ID, EQP_MODEL_NAME, MASTER_YN, PROCESS_UNIT, CUST_MODEL_OPT, DELAY_TIME, RETRY_DELAY_TIME, RETRY_COUNT "
             " FROM ISF_MODEL M "
             "WHERE M.STEP_SEQ= :step_seq"
             "  AND M.PPID IN (:ppid, 'ALL') "
             "  AND M.RECIPE_ID IN (:recipe_id, 'ALL') "
             )
    cursor.execute(query, step_seq=step_seq, ppid=ppid, RECIPE_ID=recipe_id)
    result = fetch_data_all(cursor)
    return result
@sf_dao_decorator
def get_copied_isf_templt_st(cursor, model_seq, flow_type, sensor_type, recipe_step_id, alias_rstep, transf_sensor_name):
    query = (" SELECT TEMPLT_ST_SEQ, MODEL_SEQ, SENSOR_TYPE, RECIPE_STEP_ID, TRANSF_SENSOR_NAME, ORIGIN_SENSOR_NAME_LIST, CUST_SENSOR_OPT_LIST, TRANSF_EQTN_CONT, REF_EQTN_CONT, MDL_INDEX_EQTN_CONT, DISTR_USE_STABLE_WIN_YN, DISTR_Y_SCALE_MINM_SIZE, "
             " DISTR_Y_SCALE_MAX_SIZE, REF_EVAL_WIN_SIZE, REF_EVAL_1ST_INDEX_YN, REF_EVAL_1ST_INDEX_1ST_VALN, REF_EVAL_1ST_INDEX_2ND_VALN, REF_EVAL_2ND_INDEX_YN, REF_EVAL_2ND_INDEX_1ST_VALN, REF_EVAL_2ND_INDEX_2ND_VALN, REF_EVAL_3RD_INDEX_YN, "
             " REF_EVAL_3RD_INDEX_1ST_VALN, REF_EVAL_3RD_INDEX_2ND_VALN, MINM_WAFER_CNT, USE_UPDATE_YN, AUTO_UPDATE_YN, CYCLE_AUTO_UPDATE_YN, REF_RESULT_CONT, GOLDEN_CHAMBER_ID, GOLDEN_STATUS, RSTEP_MGT_SEQ, TEMPLT_FLOW_TYPE, ALIAS_RSTEP, REF_OES_CAL "
             " FROM ISF_TEMPLT_ST TST "
             "WHERE TST.MODEL_SEQ = :model_seq "
             "  AND TEMPLT_FLOW_TYPE = :flow_type "
             "  AND SENSOR_TYPE = :sensor_type "
             "  AND RECIPE_STEP_ID = :recipe_step_id "
             "  AND TRANSF_SENSOR_NAME = :transf_sensor_name "
             )
    if alias_rstep is not None:
        query += "  AND ALIAS_RSTEP = '{ALIAS_RSTEP}' ".format(ALIAS_RSTEP=alias_rstep)
    cursor.execute(query, model_seq=model_seq, flow_type=flow_type, sensor_type=sensor_type, recipe_step_id=recipe_step_id, transf_sensor_name=transf_sensor_name)
    result = fetch_data_one(cursor)
    return result
@sf_dao_decorator
def get_copied_isf_templt_st_algrth(cursor, templt_st_seq, algrth_sensor_name):
    query = (" SELECT TEMPLT_ST_ALGRTH_SEQ, TEMPLT_ST_SEQ, ALGRTH_SENSOR_NAME, ALGRTH_NAME, ALGRTH_EQTN_CONT, TEMPLT_ST_ALGRTH_TYPE, VC_ENABLE_YN, VC_CB_FILTER_CONT, FDC_QPASS_CONFIRM_SEQ, BATCH_TYPE_WAFER_OPT_CODE, BATCH_TYPE_WAFER_OPT_SPEC "
             " FROM ISF_TEMPLT_ST_ALGRTH STA "
             "WHERE STA.TEMPLT_ST_SEQ= :templt_st_seq "
             "  AND STA.ALGRTH_SENSOR_NAME =:algrth_sensor_name "
             )
    cursor.execute(query, templt_st_seq=templt_st_seq, algrth_sensor_name=algrth_sensor_name)
    result = fetch_data_one(cursor)
    return result
@sf_dao_cud_decorator
def increment_isf_model_seq(cursor, conn, value):
    query = ("ALTER SEQUENCE ISF_MODEL_SEQ INCREMENT BY {VALUE}".format(VALUE=value))
    cursor.execute(query)
    conn.commit()
    query = ("SELECT ISF_MODEL_SEQ.NEXTVAL AS MODEL_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    query = ("ALTER SEQUENCE ISF_MODEL_SEQ INCREMENT BY 1 ")
    cursor.execute(query)
    conn.commit()
    return result.MODEL_SEQ
@sf_dao_cud_decorator
def increment_isf_mass_job_seq(cursor, conn, value):
    query = ("ALTER SEQUENCE ISF_MASS_JOB_SEQ INCREMENT BY {VALUE}".format(VALUE=value))
    cursor.execute(query)
    conn.commit()
    query = ("SELECT ISF_MASS_JOB_SEQ.NEXTVAL AS JOB_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    query = ("ALTER SEQUENCE ISF_MASS_JOB_SEQ INCREMENT BY 1 ")
    cursor.execute(query)
    conn.commit()
    return result.JOB_SEQ
@sf_dao_decorator
def generate_new_isf_mass_job_seq(cursor):
    query = ("SELECT ISF_MASS_JOB_SEQ.NEXTVAL AS JOB_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    return result.JOB_SEQ
@sf_dao_decorator
def generate_new_isf_model_seq(cursor):
    query = ("SELECT ISF_MODEL_SEQ.NEXTVAL AS MODEL_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    return result.MODEL_SEQ
@sf_dao_cud_decorator
def increment_isf_templt_st_seq(cursor, conn, value):
    query = ("ALTER SEQUENCE ISF_TEMPLT_ST_SEQ INCREMENT BY {VALUE}".format(VALUE=value))
    cursor.execute(query)
    conn.commit()
    query = ("SELECT ISF_TEMPLT_ST_SEQ.NEXTVAL AS TEMPLT_ST_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    query = ("ALTER SEQUENCE ISF_TEMPLT_ST_SEQ INCREMENT BY 1 ")
    cursor.execute(query)
    conn.commit()
    return result.TEMPLT_ST_SEQ
@sf_dao_decorator
def generate_new_isf_templt_st_seq(cursor):
    query = ("SELECT ISF_TEMPLT_ST_SEQ.NEXTVAL AS TEMPLT_ST_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    return result.TEMPLT_ST_SEQ
@sf_dao_cud_decorator
def increment_isf_templt_st_algrth_seq(cursor, conn, value):
    query = ("ALTER SEQUENCE ISF_TEMPLT_ST_ALGRTH_SEQ INCREMENT BY {VALUE}".format(VALUE=value) )
    cursor.execute(query)
    conn.commit()
    query = ("SELECT ISF_TEMPLT_ST_ALGRTH_SEQ.NEXTVAL AS TEMPLT_ST_ALGRTH_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    query = ("ALTER SEQUENCE ISF_TEMPLT_ST_ALGRTH_SEQ INCREMENT BY 1 ")
    cursor.execute(query)
    conn.commit()
    return result.TEMPLT_ST_ALGRTH_SEQ
@sf_dao_decorator
def generate_new_isf_templt_st_algrth_seq(cursor):
    query = ("SELECT ISF_TEMPLT_ST_ALGRTH_SEQ.NEXTVAL AS TEMPLT_ST_ALGRTH_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    return result.TEMPLT_ST_ALGRTH_SEQ
@sf_dao_cud_decorator
def insert_isf_model(cursor, conn, isf_model):
    query = (" INSERT INTO ISF_MODEL (MODEL_SEQ, MODEL_NAME, STEP_SEQ, PPID, RECIPE_ID, EQP_MODEL_NAME, MASTER_YN, CREATR_SEQ, CREATE_TMSTP, UPDATER_SEQ, UPDATE_TMSTP, PROCESS_UNIT, CUST_MODEL_OPT, DELAY_TIME, RETRY_DELAY_TIME, RETRY_COUNT) "
             " VALUES (:model_seq, :model_name, :step_seq, :ppid, :recipe_id, :eqp_model_name, :master_yn, -990, systimestamp, -990, systimestamp, :process_unit, :cust_model_opt, :delay_time, :retry_delay_time, :retry_count) ")
    cursor.execute(query, model_seq=isf_model.MODEL_SEQ, model_name=isf_model.MODEL_NAME, step_seq=isf_model.STEP_SEQ, ppid=isf_model.PPID, recipe_id=isf_model.RECIPE_ID, eqp_model_name=isf_model.EQP_MODEL_NAME, master_yn=isf_model.MASTER_YN,
                   process_unit=isf_model.PROCESS_UNIT, cust_model_opt=isf_model.CUST_MODEL_OPT, delay_time=isf_model.DELAY_TIME, retry_delay_time=isf_model.RETRY_DELAY_TIME, retry_count=isf_model.RETRY_COUNT)
    conn.commit()
@sf_dao_cud_decorator
def insert_isf_templt_st(cursor, conn, isf_templt_st):
    query = (" INSERT INTO ISF_TEMPLT_ST (TEMPLT_ST_SEQ, MODEL_SEQ, SENSOR_TYPE, RECIPE_STEP_ID, TRANSF_SENSOR_NAME, ORIGIN_SENSOR_NAME_LIST, CUST_SENSOR_OPT_LIST, TRANSF_EQTN_CONT, REF_EQTN_CONT, MDL_INDEX_EQTN_CONT, DISTR_USE_STABLE_WIN_YN, DISTR_Y_SCALE_MINM_SIZE, "
             " DISTR_Y_SCALE_MAX_SIZE, REF_EVAL_WIN_SIZE, REF_EVAL_1ST_INDEX_YN, REF_EVAL_1ST_INDEX_1ST_VALN, REF_EVAL_1ST_INDEX_2ND_VALN, REF_EVAL_2ND_INDEX_YN, REF_EVAL_2ND_INDEX_1ST_VALN, REF_EVAL_2ND_INDEX_2ND_VALN, REF_EVAL_3RD_INDEX_YN, REF_EVAL_3RD_INDEX_1ST_VALN, "
             " REF_EVAL_3RD_INDEX_2ND_VALN, MINM_WAFER_CNT, USE_UPDATE_YN, AUTO_UPDATE_YN, CYCLE_AUTO_UPDATE_YN, CREATR_SEQ, CREATE_TMSTP, UPDATER_SEQ, UPDATE_TMSTP, REF_RESULT_CONT, GOLDEN_CHAMBER_ID, GOLDEN_STATUS, RSTEP_MGT_SEQ, TEMPLT_FLOW_TYPE, ALIAS_RSTEP, REF_OES_CAL) "
             " VALUES (:templt_st_seq, :model_seq, :sensor_type, :recipe_step_id, :transf_sensor_name, :origin_sensor_name_list, :cust_sensor_opt_list, to_clob(:transf_eqtn_cont), to_clob(:ref_eqtn_cont), to_clob(:mdl_index_eqtn_cont), :distr_use_stable_win_yn, :distr_y_scale_minm_size, "
             " :distr_y_scale_max_size, :ref_eval_win_size, :ref_eval_1st_index_yn, :ref_eval_1st_index_1st_valn, :ref_eval_1st_index_2nd_valn, :ref_eval_2nd_index_yn, :ref_eval_2nd_index_1st_valn, :ref_eval_2nd_index_2nd_valn, :ref_eval_3rd_index_yn, :ref_eval_3rd_index_1st_valn, "
             " :ref_eval_3rd_index_2nd_valn, :minm_wafer_cnt, :use_update_yn, :auto_update_yn, :cycle_auto_update_yn, -990, systimestamp, -990, systimestamp, to_clob(:ref_result_cont), :golden_chamber_id, :golden_status, :rstep_mgt_seq, :templt_flow_type, :alias_rstep, to_clob(:ref_oes_cal) ) ")
    cursor.execute(query, templt_st_seq=isf_templt_st.TEMPLT_ST_SEQ, model_seq=isf_templt_st.MODEL_SEQ, sensor_type=isf_templt_st.SENSOR_TYPE, recipe_step_id=isf_templt_st.RECIPE_STEP_ID, transf_sensor_name=isf_templt_st.TRANSF_SENSOR_NAME, origin_sensor_name_list=isf_templt_st.ORIGIN_SENSOR_NAME_LIST,
                   cust_sensor_opt_list=isf_templt_st.CUST_SENSOR_OPT_LIST, transf_eqtn_cont=isf_templt_st.TRANSF_EQTN_CONT, ref_eqtn_cont=isf_templt_st.REF_EQTN_CONT, mdl_index_eqtn_cont=isf_templt_st.MDL_INDEX_EQTN_CONT, distr_use_stable_win_yn=isf_templt_st.DISTR_USE_STABLE_WIN_YN,
                   distr_y_scale_minm_size=isf_templt_st.DISTR_Y_SCALE_MINM_SIZE, distr_y_scale_max_size=isf_templt_st.DISTR_Y_SCALE_MAX_SIZE, ref_eval_win_size=isf_templt_st.REF_EVAL_WIN_SIZE, ref_eval_1st_index_yn=isf_templt_st.REF_EVAL_1ST_INDEX_YN, ref_eval_1st_index_1st_valn=isf_templt_st.REF_EVAL_1ST_INDEX_1ST_VALN,
                   ref_eval_1st_index_2nd_valn=isf_templt_st.REF_EVAL_1ST_INDEX_2ND_VALN, ref_eval_2nd_index_yn=isf_templt_st.REF_EVAL_2ND_INDEX_YN, ref_eval_2nd_index_1st_valn=isf_templt_st.REF_EVAL_2ND_INDEX_1ST_VALN, ref_eval_2nd_index_2nd_valn=isf_templt_st.REF_EVAL_2ND_INDEX_2ND_VALN,
                   ref_eval_3rd_index_yn=isf_templt_st.REF_EVAL_3RD_INDEX_YN, ref_eval_3rd_index_1st_valn=isf_templt_st.REF_EVAL_3RD_INDEX_1ST_VALN, ref_eval_3rd_index_2nd_valn=isf_templt_st.REF_EVAL_3RD_INDEX_2ND_VALN, minm_wafer_cnt=isf_templt_st.MINM_WAFER_CNT, use_update_yn=isf_templt_st.USE_UPDATE_YN,
                   auto_update_yn=isf_templt_st.AUTO_UPDATE_YN, cycle_auto_update_yn=isf_templt_st.CYCLE_AUTO_UPDATE_YN, ref_result_cont=isf_templt_st.REF_RESULT_CONT, golden_chamber_id=isf_templt_st.GOLDEN_CHAMBER_ID, golden_status=isf_templt_st.GOLDEN_STATUS, rstep_mgt_seq=isf_templt_st.RSTEP_MGT_SEQ,
                   templt_flow_type=isf_templt_st.TEMPLT_FLOW_TYPE, alias_rstep=isf_templt_st.ALIAS_RSTEP, ref_oes_cal=isf_templt_st.REF_OES_CAL)
    conn.commit()
@sf_dao_cud_decorator
def insert_isf_templt_st_algrth(cursor, conn, isf_templt_st_algrth):
    query = (" INSERT INTO ISF_TEMPLT_ST_ALGRTH (TEMPLT_ST_ALGRTH_SEQ, TEMPLT_ST_SEQ, ALGRTH_SENSOR_NAME, ALGRTH_NAME, ALGRTH_EQTN_CONT, CREATR_SEQ, CREATE_TMSTP, UPDATER_SEQ, UPDATE_TMSTP, TEMPLT_ST_ALGRTH_TYPE, VC_ENABLE_YN, VC_CB_FILTER_CONT, FDC_QPASS_CONFIRM_SEQ, BATCH_TYPE_WAFER_OPT_CODE, BATCH_TYPE_WAFER_OPT_SPEC) "
             " VALUES (:templt_st_algrth_seq, :templt_st_seq, :algrth_sensor_name, :algrth_name, to_clob(:algrth_eqtn_cont), -990, systimestamp, -990, systimestamp, :templt_st_algrth_type, :vc_enable_yn, :vc_cb_filter_cont, :fdc_qpass_confirm_seq, :batch_type_wafer_opt_code, :batch_type_wafer_opt_spec ) ")
    cursor.execute(query, templt_st_algrth_seq=isf_templt_st_algrth.TEMPLT_ST_ALGRTH_SEQ, templt_st_seq=isf_templt_st_algrth.TEMPLT_ST_SEQ, algrth_sensor_name=isf_templt_st_algrth.ALGRTH_SENSOR_NAME, algrth_name=isf_templt_st_algrth.ALGRTH_NAME, algrth_eqtn_cont=isf_templt_st_algrth.ALGRTH_EQTN_CONT,
                   templt_st_algrth_type=isf_templt_st_algrth.TEMPLT_ST_ALGRTH_TYPE, vc_enable_yn=isf_templt_st_algrth.VC_ENABLE_YN, vc_cb_filter_cont=isf_templt_st_algrth.VC_CB_FILTER_CONT, fdc_qpass_confirm_seq=isf_templt_st_algrth.FDC_QPASS_CONFIRM_SEQ, batch_type_wafer_opt_code=isf_templt_st_algrth.BATCH_TYPE_WAFER_OPT_CODE,
                   batch_type_wafer_opt_spec=isf_templt_st_algrth.BATCH_TYPE_WAFER_OPT_SPEC)
    conn.commit()
@sf_dao_decorator
def get_org_isf_templt_pc(cursor, templt_post_calc_seq):
    query = (" SELECT BATCH_TYPE_WAFER_OPT_CODE, BATCH_TYPE_WAFER_OPT_SPEC, CREATE_TMSTP, CREATR_SEQ, EQP_MODEL_NAME, MDL_MODEL_COL_SEQ, MODEL_SEQ, POST_CALC_EQTN_CONT, POST_CALC_RECIPE_ID, POST_CALC_RECIPE_STEP_ID, "
             "        POST_CALC_SENSOR_NAME, PPID, SA_SEQ, SENSOR_TYPE, STEP_SEQ, TEMPLT_FLOW_TYPE, TEMPLT_POST_CALC_SEQ, TEMPLT_ST_ALGRTH_SEQ_LIST, UPDATE_TMSTP, UPDATER_SEQ, VC_CB_FILTER_CONT, VC_ENABLE_YN "
             "   FROM ISF_TEMPLT_PC PC "
             "  WHERE PC.TEMPLT_POST_CALC_SEQ= :templt_post_calc_seq "
             )
    cursor.execute(query, templt_post_calc_seq=templt_post_calc_seq)
    result = fetch_data_one(cursor)
    return result
@sf_dao_decorator
def get_org_isf_templt_pc_dcol_config(cursor, templt_post_calc_seq):
    query = (" SELECT TEMPLT_POST_CALC_SEQ, VALUE_TYPE, DCOL_YN, DCOL_ITEM_NAME, DCOL_TYPE, DCOL_STEP_SEQ, SPC_GROUP_TYPE, SPC_GROUP_STEP_SEQ, DCOL_FILTER_YN, LSL_VALN, USL_VALN, DCOL_SPEC, CREATR_SEQ, CREATE_TMSTP, UPDATER_SEQ, UPDATE_TMSTP, FB_APC_YN, TRG_YN, DCOL_Y_CH_LIST "
             "   FROM ISF_TEMPLT_PC_DCOL_CONFIG PCDC "
             "  WHERE PCDC.TEMPLT_POST_CALC_SEQ= :templt_post_calc_seq "
             )
    cursor.execute(query, templt_post_calc_seq=templt_post_calc_seq)
    result = fetch_data_one(cursor)
    return result
@sf_dao_decorator
def get_copied_isf_templt_pc(cursor, model_seq, sensor_type, post_calc_recipe_step_id, post_calc_recipe_id, post_calc_sensor_name):
    query = (" SELECT BATCH_TYPE_WAFER_OPT_CODE, BATCH_TYPE_WAFER_OPT_SPEC, CREATE_TMSTP, CREATR_SEQ, EQP_MODEL_NAME, MDL_MODEL_COL_SEQ, MODEL_SEQ, POST_CALC_EQTN_CONT, POST_CALC_RECIPE_ID, POST_CALC_RECIPE_STEP_ID, "
             "        POST_CALC_SENSOR_NAME, PPID, SA_SEQ, SENSOR_TYPE, STEP_SEQ, TEMPLT_FLOW_TYPE, TEMPLT_POST_CALC_SEQ, TEMPLT_ST_ALGRTH_SEQ_LIST, UPDATE_TMSTP, UPDATER_SEQ, VC_CB_FILTER_CONT, VC_ENABLE_YN "
             " FROM ISF_TEMPLT_PC PC "
             "WHERE 1=1 "
             "  AND MODEL_SEQ = :model_seq "
             "  AND SENSOR_TYPE = :sensor_type "
             "  AND POST_CALC_RECIPE_STEP_ID = :post_calc_recipe_step_id "
             "  AND POST_CALC_RECIPE_ID = :post_calc_recipe_id "
             "  AND POST_CALC_SENSOR_NAME = :post_calc_sensor_name "
             )
    cursor.execute(query, model_seq=model_seq, sensor_type=sensor_type, post_calc_recipe_step_id=post_calc_recipe_step_id, post_calc_recipe_id=post_calc_recipe_id, post_calc_sensor_name=post_calc_sensor_name)
    result = fetch_data_one(cursor)
    return result
@sf_dao_decorator
def generate_new_isf_templt_pc_seq(cursor):
    query = ("SELECT ISF_TEMPLT_PC_SEQ.NEXTVAL AS TEMPLT_PC_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    return result.TEMPLT_PC_SEQ
@sf_dao_decorator
def get_process_unit_by_step(cursor, step_seq):
    query = ("SELECT DISTINCT PROCESS_UNIT "
             "  FROM ISF_MODEL "
             " WHERE STEP_SEQ = :step_seq ")
    cursor.execute(query, step_seq=step_seq)
    result = fetch_data_one(cursor)
    return result.PROCESS_UNIT
@sf_dao_cud_decorator
def increment_isf_templt_pc_seq(cursor, conn, value):
    query = ("ALTER SEQUENCE ISF_TEMPLT_PC_SEQ INCREMENT BY {VALUE}".format(VALUE=value) )
    cursor.execute(query)
    conn.commit()
    query = ("SELECT ISF_TEMPLT_PC_SEQ.NEXTVAL AS TEMPLT_PC_SEQ "
             "  FROM DUAL ")
    cursor.execute(query)
    result = fetch_data_one(cursor)
    query = ("ALTER SEQUENCE ISF_TEMPLT_PC_SEQ INCREMENT BY 1 ")
    cursor.execute(query)
    conn.commit()
    return result.TEMPLT_PC_SEQ
@sf_dao_cud_decorator
def insert_isf_templt_pc(cursor, conn, isf_templt_pc):
    query = (" INSERT INTO ISF_TEMPLT_PC (BATCH_TYPE_WAFER_OPT_CODE, BATCH_TYPE_WAFER_OPT_SPEC, CREATE_TMSTP, CREATR_SEQ, EQP_MODEL_NAME, MDL_MODEL_COL_SEQ, MODEL_SEQ, POST_CALC_EQTN_CONT, POST_CALC_RECIPE_ID, POST_CALC_RECIPE_STEP_ID, "
             "              POST_CALC_SENSOR_NAME, PPID, SA_SEQ, SENSOR_TYPE, STEP_SEQ, TEMPLT_FLOW_TYPE, TEMPLT_POST_CALC_SEQ, TEMPLT_ST_ALGRTH_SEQ_LIST, UPDATE_TMSTP, UPDATER_SEQ, VC_CB_FILTER_CONT, VC_ENABLE_YN) "
             " VALUES (:batch_type_wafer_opt_code, :batch_type_wafer_opt_spec, systimestamp, -990, :eqp_model_name, :mdl_model_col_seq, :model_seq, to_clob(:post_calc_eqtn_cont), :post_calc_recipe_id, :post_calc_recipe_step_id, "
             "         :post_calc_sensor_name, :ppid, :sa_seq, :sensor_type, :step_seq, :templt_flow_type, :templt_post_calc_seq, :templt_st_algrth_seq_list, systimestamp, -990, :vc_cb_filter_cont, :vc_enable_yn )")
    cursor.execute(query, batch_type_wafer_opt_code=isf_templt_pc.BATCH_TYPE_WAFER_OPT_CODE, batch_type_wafer_opt_spec=isf_templt_pc.BATCH_TYPE_WAFER_OPT_SPEC, eqp_model_name=isf_templt_pc.EQP_MODEL_NAME, mdl_model_col_seq=isf_templt_pc.MDL_MODEL_COL_SEQ,
                   model_seq=isf_templt_pc.MODEL_SEQ, post_calc_eqtn_cont=isf_templt_pc.POST_CALC_EQTN_CONT, post_calc_recipe_id=isf_templt_pc.POST_CALC_RECIPE_ID, post_calc_recipe_step_id=isf_templt_pc.POST_CALC_RECIPE_STEP_ID, post_calc_sensor_name=isf_templt_pc.POST_CALC_SENSOR_NAME,
                   ppid=isf_templt_pc.PPID, sa_seq=isf_templt_pc.SA_SEQ, sensor_type=isf_templt_pc.SENSOR_TYPE, step_seq=isf_templt_pc.STEP_SEQ, templt_flow_type=isf_templt_pc.TEMPLT_FLOW_TYPE, templt_post_calc_seq=isf_templt_pc.TEMPLT_POST_CALC_SEQ,
                   templt_st_algrth_seq_list=isf_templt_pc.TEMPLT_ST_ALGRTH_SEQ_LIST, vc_cb_filter_cont=isf_templt_pc.VC_CB_FILTER_CONT, vc_enable_yn=isf_templt_pc.VC_ENABLE_YN)
    conn.commit()
@sf_dao_cud_decorator
def insert_isf_templt_pc_dcol_config(cursor, conn, isf_templt_pc_dcol_config):
    query = (" INSERT INTO ISF_TEMPLT_PC_DCOL_CONFIG (TEMPLT_POST_CALC_SEQ, VALUE_TYPE, DCOL_YN, DCOL_ITEM_NAME, DCOL_TYPE, DCOL_STEP_SEQ, SPC_GROUP_TYPE, SPC_GROUP_STEP_SEQ, DCOL_FILTER_YN, LSL_VALN, USL_VALN, DCOL_SPEC, CREATR_SEQ, CREATE_TMSTP, UPDATER_SEQ, UPDATE_TMSTP, FB_APC_YN, TRG_YN, DCOL_Y_CH_LIST) "
             " VALUES (:templt_post_calc_seq, :value_type, :dcol_yn, :dcol_item_name, :dcol_type, :dcol_step_seq, :spc_group_type, :spc_group_step_seq, :dcol_filter_yn, :lsl_valn, :usl_valn, :dcol_spec, -990, systimestamp, -990, systimestamp, :fb_apc_yn, :trg_yn, :dcol_y_ch_list )")
    cursor.execute(query, templt_post_calc_seq=isf_templt_pc_dcol_config.TEMPLT_POST_CALC_SEQ, value_type=isf_templt_pc_dcol_config.VALUE_TYPE, dcol_yn=isf_templt_pc_dcol_config.DCOL_YN, dcol_item_name=isf_templt_pc_dcol_config.DCOL_ITEM_NAME, dcol_type=isf_templt_pc_dcol_config.DCOL_TYPE,
                   dcol_step_seq=isf_templt_pc_dcol_config.DCOL_STEP_SEQ, spc_group_type=isf_templt_pc_dcol_config.SPC_GROUP_TYPE, spc_group_step_seq=isf_templt_pc_dcol_config.SPC_GROUP_STEP_SEQ, dcol_filter_yn=isf_templt_pc_dcol_config.DCOL_FILTER_YN, lsl_valn=isf_templt_pc_dcol_config.LSL_VALN,
                   usl_valn=isf_templt_pc_dcol_config.USL_VALN, dcol_spec=isf_templt_pc_dcol_config.DCOL_SPEC, fb_apc_yn=isf_templt_pc_dcol_config.FB_APC_YN, trg_yn=isf_templt_pc_dcol_config.TRG_YN, dcol_y_ch_list=isf_templt_pc_dcol_config.DCOL_Y_CH_LIST)
    conn.commit()
@sf_dao_decorator
def get_isf_templt_st_space(cursor, model_seq, templt_st_seq):
    query = (" SELECT TEMPLT_ST_SEQ, MODEL_SEQ, DATA2D_SAVE_YN, RECIPE_STEP_NORMLZ_YN, EXCLUDE_FIRST_LAST_RSTEP_YN "
             " FROM ISF_TEMPLT_ST_SPACE SP "
             "WHERE 1=1 "
             "  AND SP.MODEL_SEQ=:model_seq "
             "  AND SP.TEMPLT_ST_SEQ= :templt_st_seq "
             )
    cursor.execute(query, model_seq=model_seq, templt_st_seq=templt_st_seq)
    result = fetch_data_one(cursor)
    return result
@sf_dao_decorator
def get_isf_rstep_norm_config(cursor, templt_st_seq, sensor_name):
    query = ("  SELECT TEMPLT_ST_SEQ, RECIPE_ID, SENSOR_NAME, RECIPE_STEP_ID, RECIPE_STEP_ID_ORDER, TARGET_RANGE, MIN_INTERVAL, NORMLZ_TYPE, EXCLUDE_YN "
             "  FROM ISF_RSTEP_NORM_CONFIG NC "
             " WHERE NC.TEMPLT_ST_SEQ =:templt_st_seq "
             "   AND NC.SENSOR_NAME =:sensor_name "
             " ORDER BY RECIPE_ID, RECIPE_STEP_ID, RECIPE_STEP_ID_ORDER "
             )
    cursor.execute(query, templt_st_seq=templt_st_seq, sensor_name=sensor_name)
    result = fetch_data_all(cursor)
    return result
@sf_dao_cud_decorator
def insert_isf_templt_st_space(cursor, conn, isf_templt_st_space):
    query = (" INSERT INTO ISF_TEMPLT_ST_SPACE (TEMPLT_ST_SEQ, MODEL_SEQ, DATA2D_SAVE_YN, CREATR_SEQ, CREATE_TMSTP, UPDATER_SEQ, UPDATE_TMSTP, RECIPE_STEP_NORMLZ_YN, EXCLUDE_FIRST_LAST_RSTEP_YN) "
             " VALUES (:templt_st_seq, :model_seq, :data2d_save_yn, -990, systimestamp, -990, systimestamp, :recipe_step_normlz_yn, :exclude_first_last_rstep_yn ) " )
    cursor.execute(query, templt_st_seq=isf_templt_st_space.TEMPLT_ST_SEQ, model_seq=isf_templt_st_space.MODEL_SEQ, data2d_save_yn=isf_templt_st_space.DATA2D_SAVE_YN, recipe_step_normlz_yn=isf_templt_st_space.RECIPE_STEP_NORMLZ_YN, exclude_first_last_rstep_yn=isf_templt_st_space.EXCLUDE_FIRST_LAST_RSTEP_YN)
    conn.commit()
@sf_dao_cud_decorator
def insert_isf_rstep_norm_config_list(cursor, conn, isf_rstep_norm_config_list):
    isf_rstep_norm_config_list =[(x.TEMPLT_ST_SEQ, x.RECIPE_ID, x.SENSOR_NAME, x.RECIPE_STEP_ID, x.RECIPE_STEP_ID_ORDER, x.TARGET_RANGE, x.MIN_INTERVAL, x.NORMLZ_TYPE, x.EXECLUDE_YN) for x in isf_rstep_norm_config_list]
    query = (" INSERT INTO ISF_RSTEP_NORM_CONFIG (TEMPLT_ST_SEQ, RECIPE_ID, SENSOR_NAME, RECIPE_STEP_ID, RECIPE_STEP_ID_ORDER, TARGET_RANGE, MIN_INTERVAL, NORMLZ_TYPE, EXECLUDE_YN) "
             " VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9 ) " )
    cursor.prepare(query)
    cursor.executemany(query, isf_rstep_norm_config_list)
    conn.commit()
@sf_dao_decorator
def get_eqp_id_by_step(cursor, step_seq, period_start_tmstp, period_end_tmstp):
    query = (" SELECT /*+ INDEX(L ISF_LOT_IX05)*/ "
             "        DISTINCT L.EQP_ID "
             "   FROM ISF_LOT L "
             "  WHERE L.STEP_SEQ = :step_seq"
             "    AND L.CREATE_TMSTP BETWEEN TO_TIMESTAMP(:period_start_tmstp, 'YYYY-MM-DD HH24:MI:SS') AND TO_TIMESTAMP(:period_end_tmstp, 'YYYY-MM-DD HH24:MI:SS') ")
    cursor.execute(query, step_seq=step_seq, period_start_tmstp=period_start_tmstp, period_end_tmstp=period_end_tmstp)
    result = fetch_data_all(cursor)
    return [x.EQP_ID for x in result]
@sf_dao_cud_decorator
def insert_isf_mass_job(cursor, conn, isf_mass_job_list):
    isf_mass_job_list = [(x.job_seq, x.model_seq, x.step_seq, x.eqp_id, x.period_start_tmstp, x.period_end_tmstp, x.job_comment, ';'.join(x.algrth_seq_list), ';'.join(x.pc_seq_list)) for x in isf_mass_job_list]
    query = (
        " INSERT INTO ISF_MASS_JOB (JOB_SEQ, JOB_STATUS_CODE, MODEL_SEQ, STEP_SEQ, EQP_ID, PPID, LOT_ID, PERIOD_START_TMSTP, PERIOD_END_TMSTP, JOB_COMMENT, CREATR_SEQ, CREATE_TMSTP, DEL_YN, ALGRTH_SEQ, PC_SEQ) "
        " VALUES (:1, 'REGIST', :2, :3, :4, '-', '-', TO_TIMESTAMP(:5, 'YYYY-MM-DD HH24:MI:SS'), TO_TIMESTAMP(:6, 'YYYY-MM-DD HH24:MI:SS'), :7, -990, SYSTIMESTAMP, 'N', TO_CLOB(:8), TO_CLOB(:9) ) ")
    cursor.prepare(query)
    cursor.executemany(query, isf_mass_job_list)
    conn.commit()
@sf_dao_decorator
def find_exist_isf_mass_job(cursor, model_seq, step_seq, eqp_id, period_start_tmstp, period_end_tmstp, seq_str):
    query = (" SELECT JOB_SEQ "
             "   FROM ISF_MASS_JOB "
             "  WHERE 1=1 "
             "    AND MODEL_SEQ =:model_seq "
             "    AND STEP_SEQ =:step_seq "
             "    AND EQP_ID =:eqp_id "
             "    AND PPID = '-' "
             "    AND LOT_ID = '-' "
             "    AND (PERIOD_START_TMSTP <= TO_TIMESTAMP(:period_start_tmstp, 'YYYY-MM-DD HH24:MI:SS') AND PERIOD_END_TMSTP >= TO_TIMESTAMP(:period_end_tmstp, 'YYYY-MM-DD HH24:MI:SS')) "
             "    AND (ALGRTH_SEQ LIKE '%'|| :seq_str || '%' OR PC_SEQ LIKE '%'|| :seq_str || '%' ) "
             "    AND JOB_STATUS_CODE IN ('PROCESSING', 'REGIST', 'FAIL(NO_MSG), COMPLETE') "
             "    AND DEL_YN = 'N' ")
    cursor.execute(query, model_seq=model_seq, step_seq=step_seq, eqp_id=eqp_id, period_start_tmstp=period_start_tmstp, period_end_tmstp=period_end_tmstp, seq_str=seq_str)
    result = fetch_data_all(cursor)
    return [x.JOB_SEQ for x in result]
if __name__ == "__main__":
    step_seq = 'WH077090'
    sensor_type = 'OES'
    recipe_step_no = '7'
    sensor_name = 'SP_077295_MHT_0610_1'
    model_seq, templt_st_seq, templt_algrth_seq = get_isf_templt_st_seq_and_algrth_seq(step_seq, sensor_type, recipe_step_no, sensor_name, db_line='P')
    print(model_seq, templt_st_seq, templt_algrth_seq)
    step_seq = 'WH120580'
    sensor_type = 'FDC'
    recipe_step_no = 'ALL'
    sensor_name = 'HEAT_H1_L1'
    model_seq, templt_post_calc_seq = get_isf_templt_post_calc_seq(step_seq, sensor_type, recipe_step_no, sensor_name)
    print(model_seq, templt_post_calc_seq)
    step_seq = 'WH046130'
    recipe_step_no = '8'
    sensor_name = 'OES_TIME_N2_L2_M1_1129'
    model_seq, templt_st_seq, templt_algrth_seq = get_isf_templt_st_seq_and_algrth_seq_2d(step_seq, recipe_step_no, sensor_name)
    print(model_seq, templt_st_seq, templt_algrth_seq)