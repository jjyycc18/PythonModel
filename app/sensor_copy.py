from common import constants
from dao import vm_dao, sf_dao
import logging
import copy
import traceback
logger = logging.getLogger(__name__)
class ReferenceModelNotFoundException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg
class TableSequenceMatchingException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg
class ISFCopyResult:
    def __init__(self, sensor_name, sensor_type, org_step_seq, copy_step_seq):
        self.sensor_name = sensor_name
        self.sensor_type = sensor_type
        self.org_step_seq = org_step_seq
        self.copy_step_seq = copy_step_seq
        self.result = None
        self.desc = None
        self.copy_db_line_list = None
        self.isf_templt_algrth_seq_list = None
        self.isf_templt_pc_seq_list = None
    def set_result(self, result):
        self.result = result
    def set_desc(self, desc):
        self.desc = desc
    def set_copy_db_line_list(self, copy_db_line_list):
        self.copy_db_line_list = copy_db_line_list
    def set_isf_templt_algrth_seq_list(self, isf_templt_algrth_seq_list):
        self.isf_templt_algrth_seq_list = isf_templt_algrth_seq_list
    def set_isf_templt_pc_seq_list(self, isf_templt_pc_seq_list):
        self.isf_templt_pc_seq_list = isf_templt_pc_seq_list
    def __repr__(self):
        return str(self.__dict__)
class ISFMassJob:
    def __init__(self, model_seq, step_seq, period_start_tmstp, period_end_tmstp, comment):
        self.job_seq = None
        self.model_seq = model_seq
        self.step_seq = step_seq
        self.eqp_id = None
        self.period_start_tmstp = period_start_tmstp
        self.period_end_tmstp = period_end_tmstp
        self.job_comment = comment
        self.algrth_seq_list = []
        self.pc_seq_list = []
    def set_job_seq(self, job_seq):
        self.job_seq = job_seq
    def set_eqp_id(self, eqp_id):
        self.eqp_id = eqp_id
    def add_algrth_seq(self, algrth_seq):
        self.algrth_seq_list.append(algrth_seq)
    def add_pc_seq(self, pc_seq):
        self.pc_seq_list.append(pc_seq)
    def __repr__(self):
        return str(self.__dict__)
def get_db_line(org_tmp_seq, copy_tmp_seq):
    site = vm_dao.get_site_info()
    copy_line_name_list = vm_dao.get_line_name_by_tmp_seq(copy_tmp_seq)
    if site != 'MEM':
        return 'P', (['P'], [copy_line_name.LINE_NAME for copy_line_name in copy_line_name_list])
    return 'P', (['P', 'H'], [copy_line_name.LINE_NAME for copy_line_name in copy_line_name_list])
def convert_isf_sensor_type(input_type):
    if input_type == constants.ISF_OES:
        return 'OES'
    if input_type == constants.ISF_FDC:
        return 'FDC'
    if input_type == constants.ISF_MDL:
        return 'MDL'
    if input_type == constants.ISF_DATA_2D:
        return 'DATA_2D'
def generate_copy_target_list(org_tmp_seq, copy_tmp_seq):
    logger.info('sensor_copy.generate_copy_target_list called. ')
    org_input_param_list = vm_dao.get_vm_space_model_tmp_input_param(org_tmp_seq)
    copy_input_param_list = vm_dao.get_vm_space_model_tmp_input_param(copy_tmp_seq)
    org_db_line, (copy_db_line_list, copy_line_name_list) = get_db_line(org_tmp_seq, copy_tmp_seq)
    copy_target_list = []
    already_exists_list = [] # 이미 생성된 센서도 mass job 등록 해야되므로 리스트 생성
    for org_input_param, copy_input_param in zip(org_input_param_list, copy_input_param_list):
        if copy_input_param.INPUT_TYPE not in [constants.ISF_OES, constants.ISF_FDC, constants.ISF_MDL, constants.ISF_DATA_2D]:
            continue
        org_step_seq = org_input_param.PROC_STEP_SEQ
        copy_step_seq = copy_input_param.PROC_STEP_SEQ
        recipe_step_no = copy_input_param.DCOLL_ITEM.split(':')[0]
        sensor_name = ':'.join(copy_input_param.DCOLL_ITEM.split(':')[1:])
        sensor_type = copy_input_param.INPUT_TYPE
        copy_target_info = (org_db_line, copy_db_line_list, org_step_seq, copy_step_seq, sensor_type, recipe_step_no, sensor_name, copy_line_name_list)
        if copy_target_info not in copy_target_list:
            if sensor_type in [constants.ISF_OES, constants.ISF_FDC, constants.ISF_MDL]:
                copy_model_seq, copy_templt_st_seq, copy_templt_st_algrth_seq = sf_dao.get_isf_templt_st_seq_and_algrth_seq(copy_step_seq, convert_isf_sensor_type(sensor_type), recipe_step_no, sensor_name, db_line=copy_db_line_list[0])
                if copy_model_seq is not None and copy_templt_st_seq is not None and copy_templt_st_algrth_seq is not None:
                    copy_result = ISFCopyResult(recipe_step_no + ":" + sensor_name, convert_isf_sensor_type(sensor_type), org_step_seq, copy_step_seq)
                    copy_result.set_isf_templt_algrth_seq_list([(copy_model_seq, copy_templt_st_seq, copy_templt_st_algrth_seq)])
                    copy_result.set_result(constants.ISF_COPY_RESULT_ALREADY_EXISTS)
                    copy_result.set_copy_db_line_list(copy_db_line_list)
                    already_exists_list.append(copy_result)
                    continue
                copy_model_seq, copy_templt_post_calc_seq = sf_dao.get_isf_templt_post_calc_seq(copy_step_seq, convert_isf_sensor_type(sensor_type), recipe_step_no, sensor_name, db_line=copy_db_line_list[0])
                if copy_model_seq is not None and copy_templt_post_calc_seq is not None:
                    copy_result = ISFCopyResult(recipe_step_no + ":" + sensor_name, convert_isf_sensor_type(sensor_type), org_step_seq, copy_step_seq)
                    copy_result.set_isf_templt_pc_seq_list([(copy_model_seq, copy_templt_post_calc_seq)])
                    copy_result.set_result(constants.ISF_COPY_RESULT_ALREADY_EXISTS)
                    copy_result.set_copy_db_line_list(copy_db_line_list)
                    already_exists_list.append(copy_result)
                    continue
                copy_target_list.append(copy_target_info)
            if sensor_type in [constants.ISF_DATA_2D]:
                copy_model_seq, copy_templt_st_seq, copy_templt_st_algrth_seq = sf_dao.get_isf_templt_st_seq_and_algrth_seq_2d(copy_step_seq, recipe_step_no, sensor_name, db_line=copy_db_line_list[0])
                if copy_model_seq is not None and copy_templt_st_seq is not None and copy_templt_st_algrth_seq is not None:
                    copy_result = ISFCopyResult(recipe_step_no + ":" + sensor_name, convert_isf_sensor_type(sensor_type), org_step_seq, copy_step_seq)
                    copy_result.set_isf_templt_algrth_seq_list([(copy_model_seq, copy_templt_st_seq, copy_templt_st_algrth_seq)])
                    copy_result.set_result(constants.ISF_COPY_RESULT_ALREADY_EXISTS)
                    copy_result.set_copy_db_line_list(copy_db_line_list)
                    already_exists_list.append(copy_result)
                    continue
                copy_target_list.append(copy_target_info)
    logger.info('sensor_copy.generate_copy_target_list : target_cnt={TARGET_CNT}'.format(TARGET_CNT=len(copy_target_list)))
    return copy_target_list, already_exists_list
def register_isf_mass_job(org_tmp_seq, copy_tmp_seq, isf_sensor_copy_result_list, period_start_tmstp, period_end_tmstp):
    logger.info('sensor_copy.register_isf_mass_job called.  '
                'org_tmp_seq={ORG_TMP_SEQ}, copy_tmp_seq={COPY_TMP_SEQ}'.format(ORG_TMP_SEQ=org_tmp_seq, COPY_TMP_SEQ=copy_tmp_seq))
    isf_mass_job_dict = {}
    for isf_sensor_copy_result in isf_sensor_copy_result_list:
        if isf_sensor_copy_result.result == constants.ISF_COPY_RESULT_FAIL:
            logger.info('sensor_copy.register_isf_mass_job : isf sensor copy failed. skip register MASS Job. '
                        'isf_sensor_copy_result={ISF_SENSOR_COPY_RESULT}'.format(ISF_SENSOR_COPY_RESULT=isf_sensor_copy_result))
            return None
        step_seq = isf_sensor_copy_result.copy_step_seq
        copy_db_line_list = isf_sensor_copy_result.copy_db_line_list
        if isf_sensor_copy_result.isf_templt_algrth_seq_list is not None:
            for (model_seq, templt_st_seq, templt_st_algrth_seq) in isf_sensor_copy_result.isf_templt_algrth_seq_list:
                key = (model_seq, step_seq, tuple(copy_db_line_list))
                if key in isf_mass_job_dict.keys():
                    isf_mass_job = isf_mass_job_dict[key]
                    isf_mass_job.add_algrth_seq(f'{templt_st_seq}|{templt_st_algrth_seq}')
                else:
                    isf_mass_job = ISFMassJob(model_seq, step_seq, period_start_tmstp, period_end_tmstp, 'REGISTERED_BY_SPACE_ISF_SENSOR_COPY')
                    isf_mass_job.add_algrth_seq(f'{templt_st_seq}|{templt_st_algrth_seq}')
                    isf_mass_job_dict[key] = isf_mass_job
        if isf_sensor_copy_result.isf_templt_pc_seq_list is not None:
            for (model_seq, templt_pc_seq) in isf_sensor_copy_result.isf_templt_pc_seq_list:
                key = (model_seq, step_seq, tuple(copy_db_line_list))
                if key in isf_mass_job_dict.keys():
                    isf_mass_job = isf_mass_job_dict[key]
                    isf_mass_job.add_pc_seq(str(templt_pc_seq))
                else:
                    isf_mass_job = ISFMassJob(model_seq, step_seq, period_start_tmstp, period_end_tmstp, 'REGISTERED_BY_SPACE_ISF_SENSOR_COPY')
                    isf_mass_job.add_pc_seq(str(templt_pc_seq))
                    isf_mass_job_dict[key] = isf_mass_job
    pt_new_isf_mass_job_list = []
    hq_new_isf_mass_job_list = []
    for (model_seq, step_seq, copy_db_line_list), isf_mass_job in isf_mass_job_dict.items():
        for copy_db_line in list(copy_db_line_list):
            eqp_id_list = sf_dao.get_eqp_id_by_step(step_seq, isf_mass_job.period_start_tmstp, isf_mass_job.period_end_tmstp, db_line=copy_db_line)
            for eqp_id in eqp_id_list:
                new_isf_mass_job = copy.deepcopy(isf_mass_job)
                new_isf_mass_job.set_eqp_id(eqp_id)
                for idx, algrth_seq_str in enumerate(new_isf_mass_job.algrth_seq_list[:]):
                    exists_job_list = sf_dao.find_exist_isf_mass_job(new_isf_mass_job.model_seq, new_isf_mass_job.step_seq, new_isf_mass_job.eqp_id, new_isf_mass_job.period_start_tmstp, new_isf_mass_job.period_end_tmstp, algrth_seq_str, db_line=copy_db_line)
                    if exists_job_list is not None and len(exists_job_list) > 0:
                        logger.info('already registered algrth_seq. '
                                    'model_seq={MODEL_SEQ}, step_seq={STEP_SEQ}, eqp_id={EQP_ID}, period_start_tmstp={PERIOD_START_TMSTP}, period_end_tmstp={PERIOD_END_TMSTP}, algrth_seq_str={ALGRTH_SEQ_STR}'
                                    .format(MODEL_SEQ=new_isf_mass_job.model_seq, STEP_SEQ=new_isf_mass_job.step_seq, EQP_ID=new_isf_mass_job.eqp_id, PERIOD_START_TMSTP=new_isf_mass_job.period_start_tmstp, PERIOD_END_TMSTP=new_isf_mass_job.period_end_tmstp, ALGRTH_SEQ_STR=algrth_seq_str))
                        del new_isf_mass_job.algrth_seq_list[idx]
                for idx, pc_seq_str in enumerate(new_isf_mass_job.pc_seq_list[:]):
                    exists_job_list = sf_dao.find_exist_isf_mass_job(new_isf_mass_job.model_seq, new_isf_mass_job.step_seq, new_isf_mass_job.eqp_id, new_isf_mass_job.period_start_tmstp, new_isf_mass_job.period_end_tmstp, pc_seq_str, db_line=copy_db_line)
                    if exists_job_list is not None and len(exists_job_list) > 0:
                        logger.info('already registered algrth_seq. '
                                    'model_seq={MODEL_SEQ}, step_seq={STEP_SEQ}, eqp_id={EQP_ID}, period_start_tmstp={PERIOD_START_TMSTP}, period_end_tmstp={PERIOD_END_TMSTP}, pc_seq_str={PC_SEQ_STR}'
                                    .format(MODEL_SEQ=new_isf_mass_job.model_seq, STEP_SEQ=new_isf_mass_job.step_seq, EQP_ID=new_isf_mass_job.eqp_id, PERIOD_START_TMSTP=new_isf_mass_job.period_start_tmstp, PERIOD_END_TMSTP=new_isf_mass_job.period_end_tmstp, PC_SEQ_STR=pc_seq_str))
                        del new_isf_mass_job.pc_seq_list[idx]
                if len(new_isf_mass_job.algrth_seq_list) == 0 and len(new_isf_mass_job.pc_seq_list) == 0:
                    logger.info('all isf sensors are already registered. '
                                'model_seq={MODEL_SEQ}, step_seq={STEP_SEQ}, eqp_id={EQP_ID}, period_start_tmstp={PERIOD_START_TMSTP}, period_end_tmstp={PERIOD_END_TMSTP} '
                                .format(MODEL_SEQ=new_isf_mass_job.model_seq, STEP_SEQ=new_isf_mass_job.step_seq, EQP_ID=new_isf_mass_job.eqp_id, PERIOD_START_TMSTP=new_isf_mass_job.period_start_tmstp, PERIOD_END_TMSTP=new_isf_mass_job.period_end_tmstp))
                    continue
                new_isf_mass_job.set_job_seq(generate_new_isf_mass_job_seq())
                if copy_db_line == 'P':
                    pt_new_isf_mass_job_list.append(new_isf_mass_job)
                else:
                    hq_new_isf_mass_job_list.append(new_isf_mass_job)
    if len(pt_new_isf_mass_job_list) > 0:
        sf_dao.insert_isf_mass_job(pt_new_isf_mass_job_list, db_line='P')
    if len(hq_new_isf_mass_job_list) > 0:
        sf_dao.insert_isf_mass_job(hq_new_isf_mass_job_list, db_line='H')
    mass_job_result = []
    mass_job_result.extend(pt_new_isf_mass_job_list)
    mass_job_result.extend(hq_new_isf_mass_job_list)
    logger.info('sensor_copy.register_isf_mass_job completed. '
                'pt_mass_job_cnt={PT_CNT}, hq_mass_job_cnt={HQ_CNT}'.format(PT_CNT=len(pt_new_isf_mass_job_list), HQ_CNT=len(hq_new_isf_mass_job_list)))
    return mass_job_result
def execute_isf_sensor_copy(org_tmp_seq, copy_tmp_seq):
    logger.info('sensor_copy.execute_isf_sensor_copy called. '
                'org_tmp_seq={ORG_TMP_SEQ}, copy_tmp_seq={COPY_TMP_SEQ}'.format(ORG_TMP_SEQ=org_tmp_seq, COPY_TMP_SEQ=copy_tmp_seq))
    copy_target_list, already_exists_list = generate_copy_target_list(org_tmp_seq, copy_tmp_seq)
    copy_result_list = []
    copy_result_list.extend(already_exists_list)
    for org_db_line, copy_db_line_list, org_step_seq, copy_step_seq, sensor_type, recipe_step_no, sensor_name, copy_line_name_list in copy_target_list:
        copy_result = ISFCopyResult(recipe_step_no + ":" + sensor_name, convert_isf_sensor_type(sensor_type), org_step_seq, copy_step_seq)
        logger.info('sensor_copy.execute_isf_sensor_copy : start copy '
                    'sensor_name={SENSOR_NAME}, sensor_type={SENSOR_TYPE}, org_step_seq={ORG_STEP_SEQ}'.format(SENSOR_NAME=copy_result.sensor_name, SENSOR_TYPE=copy_result.sensor_type, ORG_STEP_SEQ=copy_result.org_step_seq))
        try :
            if sensor_type in [constants.ISF_OES, constants.ISF_FDC, constants.ISF_MDL]:
                org_model_seq, org_templt_st_seq, org_templt_st_algrth_seq = sf_dao.get_isf_templt_st_seq_and_algrth_seq(org_step_seq, convert_isf_sensor_type(sensor_type), recipe_step_no, sensor_name, db_line=org_db_line)
                if org_model_seq is not None and org_templt_st_seq is not None and org_templt_st_algrth_seq is not None:
                    logger.info('execute_isf_sensor_copy : isf model detected. '
                                'sensor_name={SENSOR_NAME}, sensor_type={SENSOR_TYPE}, org_step_seq={ORG_STEP_SEQ}'.format(SENSOR_NAME=copy_result.sensor_name, SENSOR_TYPE=copy_result.sensor_type, ORG_STEP_SEQ=copy_result.org_step_seq))
                    copy_templt_algrth_seq_list = copy_isf_templt_algrth_model(org_model_seq, org_templt_st_seq, org_templt_st_algrth_seq, copy_step_seq, org_db_line, copy_db_line_list, copy_line_name_list)
                    copy_result.set_result(constants.ISF_COPY_RESULT_PASS)
                    copy_result.set_copy_db_line_list(copy_db_line_list)
                    copy_result.set_isf_templt_algrth_seq_list(copy_templt_algrth_seq_list)
                    continue
                org_model_seq, org_templt_post_calc_seq = sf_dao.get_isf_templt_post_calc_seq(org_step_seq, convert_isf_sensor_type(sensor_type), recipe_step_no, sensor_name, db_line=org_db_line)
                if org_model_seq is not None and org_templt_post_calc_seq is not None:
                    logger.info('execute_isf_sensor_copy : isf post calc model detected. '
                                'sensor_name={SENSOR_NAME}, sensor_type={SENSOR_TYPE}, org_step_seq={ORG_STEP_SEQ}'.format(SENSOR_NAME=copy_result.sensor_name, SENSOR_TYPE=copy_result.sensor_type, ORG_STEP_SEQ=copy_result.org_step_seq))
                    copy_templt_pc_seq_list = copy_isf_post_calc_model(org_model_seq, org_templt_post_calc_seq, copy_step_seq, org_db_line, copy_db_line_list, copy_line_name_list)
                    copy_result.set_result(constants.ISF_COPY_RESULT_PASS)
                    copy_result.set_copy_db_line_list(copy_db_line_list)
                    copy_result.set_isf_templt_pc_seq_list(copy_templt_pc_seq_list)
                    continue
                raise ReferenceModelNotFoundException('cannot find reference model. '
                                                      'sensor_name={SENSOR_NAME}, sensor_type={SENSOR_TYPE}, org_step_seq={ORG_STEP_SEQ}'.format(SENSOR_NAME=copy_result.sensor_name, SENSOR_TYPE=copy_result.sensor_type, ORG_STEP_SEQ=copy_result.org_step_seq))
            if sensor_type in [constants.ISF_DATA_2D]:
                org_model_seq, org_templt_st_seq, org_templt_st_algrth_seq = sf_dao.get_isf_templt_st_seq_and_algrth_seq_2d(org_step_seq, recipe_step_no, sensor_name, db_line=org_db_line)
                if org_model_seq is not None and org_templt_st_seq is not None and org_templt_st_algrth_seq is not None:
                    logger.info('execute_isf_sensor_copy : isf 2d model detected. '
                                'sensor_name={SENSOR_NAME}, sensor_type={SENSOR_TYPE}, org_step_seq={ORG_STEP_SEQ}'.format(SENSOR_NAME=copy_result.sensor_name, SENSOR_TYPE=copy_result.sensor_type, ORG_STEP_SEQ=copy_result.org_step_seq))
                    copy_2d_templt_algrth_seq_list = copy_isf_2d_model(org_model_seq, org_templt_st_seq, org_templt_st_algrth_seq, copy_step_seq, org_db_line, copy_db_line_list, copy_line_name_list)
                    copy_result.set_result(constants.ISF_COPY_RESULT_PASS)
                    copy_result.set_copy_db_line_list(copy_db_line_list)
                    copy_result.set_isf_templt_algrth_seq_list(copy_2d_templt_algrth_seq_list)
                else:
                    raise ReferenceModelNotFoundException('cannot find reference model. '
                                                          'sensor_name={SENSOR_NAME}, sensor_type={SENSOR_TYPE}, org_step_seq={ORG_STEP_SEQ}'.format(SENSOR_NAME=copy_result.sensor_name, SENSOR_TYPE=copy_result.sensor_type, ORG_STEP_SEQ=copy_result.org_step_seq))
        except ReferenceModelNotFoundException as e:
            logger.error('execute_isf_sensor_copy : ReferenceModelNotFoundException. {ERROR_MSG}'.format(ERROR_MSG=str(e)))
            copy_result.set_result(constants.ISF_COPY_RESULT_FAIL)
            copy_result.set_desc(str(e))
        except Exception as e:
            logger.exception('execute_isf_sensor_copy : unexcpected exception is occurred. ')
            copy_result.set_result(constants.ISF_COPY_RESULT_FAIL)
            copy_result.set_desc(traceback.format_exc())
        finally:
            copy_result_list.append(copy_result)
    logger.info('sensor_copy.execute_isf_sensor_copy completed. '
                'target_cnt={TARGET_CNT}, pass_cnt={PASS_CNT}, exists_cnt={EXISTS_CNT}'.format(TARGET_CNT=len(copy_target_list), PASS_CNT=len(list(filter(lambda x: x.result == constants.ISF_COPY_RESULT_PASS, copy_result_list))), EXISTS_CNT=len(already_exists_list)))
    return copy_result_list
def generate_new_isf_mass_job_seq():
    pt_new_isf_mass_job_seq = sf_dao.generate_new_isf_mass_job_seq(db_line='P')
    hq_new_isf_mass_job_seq = sf_dao.generate_new_isf_mass_job_seq(db_line='H')
    if pt_new_isf_mass_job_seq == hq_new_isf_mass_job_seq:
        return pt_new_isf_mass_job_seq
    if pt_new_isf_mass_job_seq != hq_new_isf_mass_job_seq:
        seq_diff = abs(pt_new_isf_mass_job_seq - hq_new_isf_mass_job_seq)
        if pt_new_isf_mass_job_seq > hq_new_isf_mass_job_seq:
            pt_new_isf_mass_job_seq = sf_dao.increment_isf_mass_job_seq(10, db_line='P')
            hq_new_isf_mass_job_seq = sf_dao.increment_isf_mass_job_seq(10 + seq_diff, db_line='H')
        else:
            pt_new_isf_mass_job_seq = sf_dao.increment_isf_mass_job_seq(10 + seq_diff, db_line='P')
            hq_new_isf_mass_job_seq = sf_dao.increment_isf_mass_job_seq(10, db_line='H')
        if pt_new_isf_mass_job_seq == hq_new_isf_mass_job_seq:
            return pt_new_isf_mass_job_seq
        else:
            raise Exception
def generate_new_isf_model_seq():
    pt_new_isf_model_seq = sf_dao.generate_new_isf_model_seq(db_line='P')
    hq_new_isf_model_seq = sf_dao.generate_new_isf_model_seq(db_line='H')
    if pt_new_isf_model_seq == hq_new_isf_model_seq:
        return pt_new_isf_model_seq
    if pt_new_isf_model_seq != hq_new_isf_model_seq:
        seq_diff = abs(pt_new_isf_model_seq - hq_new_isf_model_seq)
        if pt_new_isf_model_seq > hq_new_isf_model_seq:
            pt_new_isf_model_seq = sf_dao.increment_isf_model_seq(10, db_line='P')
            hq_new_isf_model_seq = sf_dao.increment_isf_model_seq(10 + seq_diff, db_line='H')
        else:
            pt_new_isf_model_seq = sf_dao.increment_isf_model_seq(10 + seq_diff, db_line='P')
            hq_new_isf_model_seq = sf_dao.increment_isf_model_seq(10, db_line='H')
        if pt_new_isf_model_seq == hq_new_isf_model_seq:
            return pt_new_isf_model_seq
        else:
            raise Exception
def generate_new_isf_templt_st_seq():
    pt_new_templt_st_seq = sf_dao.generate_new_isf_templt_st_seq(db_line='P')
    hq_new_templt_st_seq = sf_dao.generate_new_isf_templt_st_seq(db_line='H')
    if pt_new_templt_st_seq == hq_new_templt_st_seq:
        return pt_new_templt_st_seq
    if pt_new_templt_st_seq != hq_new_templt_st_seq:
        seq_diff = abs(pt_new_templt_st_seq - hq_new_templt_st_seq)
        if pt_new_templt_st_seq > hq_new_templt_st_seq:
            pt_new_templt_st_seq = sf_dao.increment_isf_templt_st_seq(10, db_line='P')
            hq_new_templt_st_seq = sf_dao.increment_isf_templt_st_seq(10 + seq_diff, db_line='H')
        else:
            pt_new_templt_st_seq = sf_dao.increment_isf_templt_st_seq(10 + seq_diff, db_line='P')
            hq_new_templt_st_seq = sf_dao.increment_isf_templt_st_seq(10, db_line='H')
        if pt_new_templt_st_seq == hq_new_templt_st_seq:
            return pt_new_templt_st_seq
        else:
            raise Exception
def generate_new_isf_templt_st_algrth_seq():
    pt_new_templt_st_algrth_seq = sf_dao.generate_new_isf_templt_st_algrth_seq(db_line='P')
    hq_new_templt_st_algrth_seq = sf_dao.generate_new_isf_templt_st_algrth_seq(db_line='H')
    if pt_new_templt_st_algrth_seq == hq_new_templt_st_algrth_seq:
        return pt_new_templt_st_algrth_seq
    if pt_new_templt_st_algrth_seq != hq_new_templt_st_algrth_seq:
        seq_diff = abs(pt_new_templt_st_algrth_seq - hq_new_templt_st_algrth_seq)
        if pt_new_templt_st_algrth_seq > hq_new_templt_st_algrth_seq:
            pt_new_templt_st_algrth_seq = sf_dao.increment_isf_templt_st_algrth_seq(10, db_line='P')
            hq_new_templt_st_algrth_seq = sf_dao.increment_isf_templt_st_algrth_seq(10 + seq_diff, db_line='H')
        else:
            pt_new_templt_st_algrth_seq = sf_dao.increment_isf_templt_st_algrth_seq(10 + seq_diff, db_line='P')
            hq_new_templt_st_algrth_seq = sf_dao.increment_isf_templt_st_algrth_seq(10, db_line='H')
        if pt_new_templt_st_algrth_seq == hq_new_templt_st_algrth_seq:
            return pt_new_templt_st_algrth_seq
        else:
            raise Exception
def copy_isf_model(org_isf_model, copy_step_seq, copy_db_line_list, copy_line_name_list):
    logger.info('sensor_copy.copy_isf_model called. ')
    copy_isf_model_seq_list = []
    candidate_copied_isf_model_list = sf_dao.get_copied_isf_model_list(copy_step_seq, org_isf_model.PPID, org_isf_model.RECIPE_ID, db_line=copy_db_line_list[0])
    org_line_name, org_maker, org_eqp_model = org_isf_model.EQP_MODEL_NAME.split('@')
    for copied_isf_model in candidate_copied_isf_model_list:
        copied_line_name, copied_maker, copied_eqp_model = copied_isf_model.EQP_MODEL_NAME.split('@')
        if copied_line_name != 'ALL' and copied_line_name not in copy_line_name_list:
            logger.info('sensor_copy.copy_isf_model : line_name is not matched.')
            continue
        if copied_maker != 'ALL' and copied_maker != org_maker:
            logger.info('sensor_copy.copy_isf_model : maker is not matched.')
            continue
        if copied_eqp_model != 'ALL' and copied_eqp_model != org_eqp_model:
            logger.info('sensor_copy.copy_isf_model : eqp_model is not matched.')
            continue
        copy_isf_model_seq_list.append(copied_isf_model.MODEL_SEQ)
    if len(copy_isf_model_seq_list) > 0:
        logger.info('sensor_copy.copy_isf_model : copy target ISF_MODEL found. '
                    'copy_isf_model_seq_list={MODEL_SEQ_LIST}'.format(MODEL_SEQ_LIST=copy_isf_model_seq_list))
    else:
        copy_model_seq = generate_new_isf_model_seq()
        copied_isf_model = copy.deepcopy(org_isf_model)
        copied_isf_model.MODEL_SEQ = copy_model_seq
        copied_isf_model.STEP_SEQ = copy_step_seq
        copied_isf_model.MODEL_NAME = copied_isf_model.MODEL_NAME + '_ISF_SENSOR_COPY_{ORG_MODEL_SEQ}'.format(
            ORG_MODEL_SEQ=org_isf_model.MODEL_SEQ)
        copied_isf_model.PPID = 'ALL'
        copied_isf_model.RECIPE_ID = 'ALL'
        copied_isf_model.EQP_MODEL_NAME = 'ALL@ALL@ALL'
        copy_process_unit = sf_dao.get_process_unit_by_step(copy_step_seq, db_line=copy_db_line_list[0])
        if copy_process_unit is not None:
            copied_isf_model.PROCESS_UNIT = copy_process_unit
        for copy_db_line in copy_db_line_list:
            sf_dao.insert_isf_model(copied_isf_model, db_line=copy_db_line)
        logger.info('sensor_copy.copy_isf_model : cannot find ISF_MODEL. create new one. '
                    'model_seq={MODEL_SEQ}'.format(MODEL_SEQ=copy_model_seq))
        copy_isf_model_seq_list.append(copied_isf_model.MODEL_SEQ)
    logger.info('sensor_copy.copy_isf_model completed. '
                'copy_isf_model_seq_list={MODEL_SEQ_LIST}'.format(MODEL_SEQ_LIST=copy_isf_model_seq_list))
    return copy_isf_model_seq_list
def copy_isf_templt_algrth_model(org_model_seq, org_templt_st_seq, org_templt_st_algrth_seq, copy_step_seq, org_db_line, copy_db_line_list, copy_line_name_list):
    logger.info('sensor_copy.copy_isf_templt_algrth_model called. ')
    org_isf_model = sf_dao.get_org_isf_model(org_model_seq, db_line=org_db_line)
    org_isf_templt_st = sf_dao.get_org_isf_templt_st(org_templt_st_seq, db_line=org_db_line)
    org_isf_templt_st_algrth = sf_dao.get_org_isf_templt_st_algrth(org_templt_st_algrth_seq, db_line=org_db_line)
    copy_isf_model_seq_list = copy_isf_model(org_isf_model, copy_step_seq, copy_db_line_list, copy_line_name_list)
    result_list = []
    for copy_model_seq in copy_isf_model_seq_list:
        copy_isf_templt_st = sf_dao.get_copied_isf_templt_st(copy_model_seq, org_isf_templt_st.TEMPLT_FLOW_TYPE, org_isf_templt_st.SENSOR_TYPE, org_isf_templt_st.RECIPE_STEP_ID, org_isf_templt_st.ALIAS_RSTEP, org_isf_templt_st.TRANSF_SENSOR_NAME, db_line=copy_db_line_list[0])
        if copy_isf_templt_st.TEMPLT_ST_SEQ is not None:
            copy_templt_st_seq = copy_isf_templt_st.TEMPLT_ST_SEQ
            logger.info('sensor_copy.copy_isf_templt_algrth_model : already exists ISF_TEMPLT_ST. '
                        'templt_st_seq={TEMPLT_ST_SEQ}'.format(TEMPLT_ST_SEQ=copy_templt_st_seq))
        else:
            copy_templt_st_seq = generate_new_isf_templt_st_seq()
            copied_isf_templt_st = copy.deepcopy(org_isf_templt_st)
            copied_isf_templt_st.MODEL_SEQ = copy_model_seq
            copied_isf_templt_st.TEMPLT_ST_SEQ = copy_templt_st_seq
            for copy_db_line in copy_db_line_list:
                sf_dao.insert_isf_templt_st(copied_isf_templt_st, db_line=copy_db_line)
            logger.info('sensor_copy.copy_isf_templt_algrth_model : insert ISF_TEMPLT_ST completed. '
                        'templt_st_seq={TEMPLT_ST_SEQ}'.format(TEMPLT_ST_SEQ=copy_templt_st_seq))
        copy_isf_templt_st_algrth = sf_dao.get_copied_isf_templt_st_algrth(copy_templt_st_seq, org_isf_templt_st_algrth.ALGRTH_SENSOR_NAME, db_line=copy_db_line_list[0])
        if copy_isf_templt_st_algrth.TEMPLT_ST_ALGRTH_SEQ is not None:
            copy_templt_st_algrth_seq = copy_isf_templt_st_algrth.TEMPLT_ST_ALGRTH_SEQ
            logger.info('sensor_copy.copy_isf_templt_algrth_model : already exists ISF_TEMPLT_ST_ALGRTH. '
                        'templt_st_algrth_seq={TEMPLT_ST_ALGRTH_SEQ}'.format(TEMPLT_ST_ALGRTH_SEQ=copy_templt_st_algrth_seq))
        else:
            copy_templt_st_algrth_seq = generate_new_isf_templt_st_algrth_seq()
            copied_isf_templt_st_algrth = copy.deepcopy(org_isf_templt_st_algrth)
            copied_isf_templt_st_algrth.TEMPLT_ST_ALGRTH_SEQ = copy_templt_st_algrth_seq
            copied_isf_templt_st_algrth.TEMPLT_ST_SEQ = copy_templt_st_seq
            for copy_db_line in copy_db_line_list:
                sf_dao.insert_isf_templt_st_algrth(copied_isf_templt_st_algrth, db_line=copy_db_line)
            logger.info('sensor_copy.copy_isf_templt_algrth_model : insert ISF_TEMPLT_ST_ALGRTH completed. '
                        'templt_st_algrth_seq={TEMPLT_ST_ALGRTH_SEQ}'.format(TEMPLT_ST_ALGRTH_SEQ=copy_templt_st_algrth_seq))
        result_list.append((copy_model_seq, copy_templt_st_seq, copy_templt_st_algrth_seq))
    logger.info('sensor_copy.copy_isf_templt_algrth_model completed. ')
    return result_list
def copy_isf_post_calc_model(org_model_seq, org_templt_post_calc_seq, copy_step_seq, org_db_line, copy_db_line_list, copy_line_name_list):
    logger.info('sensor_copy.copy_isf_post_calc_model called. ')
    org_isf_model = sf_dao.get_org_isf_model(org_model_seq, db_line=org_db_line)
    org_isf_templt_pc = sf_dao.get_org_isf_templt_pc(org_templt_post_calc_seq, db_line=org_db_line)
    org_isf_templt_pc_dcol_config = sf_dao.get_org_isf_templt_pc_dcol_config(org_templt_post_calc_seq, db_line=org_db_line)
    copy_isf_model_seq_list = copy_isf_model(org_isf_model, copy_step_seq, copy_db_line_list, copy_line_name_list)
    result_list = []
    for copy_model_seq in copy_isf_model_seq_list:
        copied_isf_templt_pc = sf_dao.get_copied_isf_templt_pc(copy_model_seq, org_isf_templt_pc.SENSOR_TYPE, org_isf_templt_pc.POST_CALC_RECIPE_STEP_ID, org_isf_templt_pc.POST_CALC_RECIPE_ID, org_isf_templt_pc.POST_CALC_SENSOR_NAME, db_line=copy_db_line_list[0])
        if copied_isf_templt_pc.TEMPLT_POST_CALC_SEQ is not None:
            copy_templt_pc_seq = copied_isf_templt_pc.TEMPLT_POST_CALC_SEQ
            logger.info('sensor_copy.copy_isf_post_calc_model : already exists ISF_TEMPLT_PC. '
                         'templt_pc_seq={TEMPLT_PC_SEQ}'.format(TEMPLT_PC_SEQ=copy_templt_pc_seq))
            return copy_model_seq, copy_templt_pc_seq
        copy_templt_pc_seq = generate_new_isf_templt_pc_seq()
        copied_isf_templt_pc = copy.deepcopy(org_isf_templt_pc)
        copied_isf_templt_pc.TEMPLT_POST_CALC_SEQ = copy_templt_pc_seq
        copied_isf_templt_pc.MODEL_SEQ = copy_model_seq
        copied_isf_templt_pc.STEP_SEQ = copy_step_seq
        copied_isf_templt_pc_dcol_config = copy.deepcopy(org_isf_templt_pc_dcol_config)
        copied_isf_templt_pc_dcol_config.TEMPLT_POST_CALC_SEQ = copy_templt_pc_seq
        copied_isf_templt_pc_dcol_config.DCOL_ITEM_NAME = None
        copied_isf_templt_pc_dcol_config.DCOL_YN = 'N'
        copied_isf_templt_pc_dcol_config.DCOL_STEP_SEQ = copy_step_seq
        copied_isf_templt_pc_dcol_config.SPC_GROUP_STEP_SEQ = copy_step_seq
        for copy_db_line in copy_db_line_list:
            sf_dao.insert_isf_templt_pc(copied_isf_templt_pc, db_line=copy_db_line)
        logger.info('sensor_copy.copy_isf_post_calc_model : insert ISF_TEMPLT_PC completed. '
                    'templt_pc_seq={TEMPLT_PC_SEQ}'.format(TEMPLT_PC_SEQ=copy_templt_pc_seq))
        for copy_db_line in copy_db_line_list:
            sf_dao.insert_isf_templt_pc_dcol_config(copied_isf_templt_pc_dcol_config, db_line=copy_db_line)
        logger.info('sensor_copy.copy_isf_post_calc_model : insert ISF_TEMPLT_PC_DCOL_CONFIG completed. '
                    'templt_pc_seq={TEMPLT_PC_SEQ}'.format(TEMPLT_PC_SEQ=copy_templt_pc_seq))
        result_list.append((copy_model_seq, copy_templt_pc_seq))
        for post_calc_eqtn_split_1 in copied_isf_templt_pc.POST_CALC_EQTN_CONT.split('^VALUE'):
            if post_calc_eqtn_split_1.count('^') == 2:
                logger.info('sensor_copy.copy_isf_post_calc_model : parse post calc equation. '
                            'equation={EQTN}'.format(EQTN=post_calc_eqtn_split_1))
                post_calc_eqtn_split_2 = post_calc_eqtn_split_1.split('^')
                sub_recipe_step_no = post_calc_eqtn_split_2[1]
                sub_algrth_sensor_name = post_calc_eqtn_split_2[2]
                copy_model_seq, copy_templt_st_seq, copy_templt_st_algrth_seq = sf_dao.get_isf_templt_st_seq_and_algrth_seq_by_model_seq(copy_model_seq, copy_step_seq, sub_recipe_step_no, sub_algrth_sensor_name, db_line=copy_db_line_list[0])
                if copy_model_seq is not None and copy_templt_st_seq is not None and copy_templt_st_algrth_seq is not None:
                    logger.info('copy_isf_post_calc_model : post calc equation input sensor already exists. '
                                'sensor_name={SENSOR_NAME}'.format(SENSOR_NAME=sub_recipe_step_no + ':' + sub_algrth_sensor_name))
                    continue
                else:
                    sub_org_model_seq, sub_org_templt_st_seq, sub_org_templt_st_algrth_seq = sf_dao.get_isf_templt_st_seq_and_algrth_seq_by_model_seq(org_model_seq, org_isf_model.STEP_SEQ, sub_recipe_step_no, sub_algrth_sensor_name, db_line=org_db_line)
                    if sub_org_model_seq is not None and sub_org_templt_st_seq is not None and sub_org_templt_st_algrth_seq is not None:
                        logger.info('copy_isf_post_calc_model : copy post calc equation input sensor. '
                                    'sensor_name={SENSOR_NAME}'.format(SENSOR_NAME=sub_recipe_step_no + ':' + sub_algrth_sensor_name))
                        copy_isf_templt_algrth_model(sub_org_model_seq, sub_org_templt_st_seq, sub_org_templt_st_algrth_seq, copy_step_seq, org_db_line, copy_db_line_list, copy_line_name_list)
    logger.info('sensor_copy.copy_isf_post_calc_model completed. ')
    return result_list
def generate_new_isf_templt_pc_seq():
    pt_new_templt_pc_seq = sf_dao.generate_new_isf_templt_pc_seq(db_line='P')
    hq_new_templt_pc_seq = sf_dao.generate_new_isf_templt_pc_seq(db_line='H')
    if pt_new_templt_pc_seq == hq_new_templt_pc_seq:
        return pt_new_templt_pc_seq
    if pt_new_templt_pc_seq != hq_new_templt_pc_seq:
        seq_diff = abs(pt_new_templt_pc_seq - hq_new_templt_pc_seq)
        if pt_new_templt_pc_seq > hq_new_templt_pc_seq:
            pt_new_templt_pc_seq = sf_dao.increment_isf_templt_pc_seq(10, db_line='P')
            hq_new_templt_pc_seq = sf_dao.increment_isf_templt_pc_seq(10 + seq_diff, db_line='H')
        else:
            pt_new_templt_pc_seq = sf_dao.increment_isf_templt_pc_seq(10 + seq_diff, db_line='P')
            hq_new_templt_pc_seq = sf_dao.increment_isf_templt_pc_seq(10, db_line='H')
        if pt_new_templt_pc_seq == hq_new_templt_pc_seq:
            return pt_new_templt_pc_seq
        else:
            raise Exception
def copy_isf_2d_model(org_model_seq, org_templt_st_seq, org_templt_st_algrth_seq, copy_step_seq, org_db_line, copy_db_line_list, copy_line_name_list):
    logger.info('sensor_copy.copy_isf_2d_model called. ')
    copy_isf_model_list = copy_isf_templt_algrth_model(org_model_seq, org_templt_st_seq, org_templt_st_algrth_seq, copy_step_seq, org_db_line, copy_db_line_list, copy_line_name_list)
    for copy_model_seq, copy_templt_st_seq, copy_templt_st_algrth_seq in copy_isf_model_list:
        org_isf_templt_st_space = sf_dao.get_isf_templt_st_space(org_model_seq, org_templt_st_seq, db_line=org_db_line)
        copy_isf_templt_st_space = sf_dao.get_isf_templt_st_space(copy_model_seq, copy_templt_st_seq, db_line=copy_db_line_list[0])
        if copy_isf_templt_st_space.TEMPLT_ST_SEQ is not None:
            logger.info('sensor_copy.copy_isf_2d_model : already exists ISF_TEMPLT_ST_SPACE. '
                         'templt_st_seq={TEMPLT_ST_SEQ}'.format(TEMPLT_ST_SEQ=copy_templt_st_seq))
        else:
            copy_isf_templt_st_space = copy.deepcopy(org_isf_templt_st_space)
            copy_isf_templt_st_space.TEMPLT_ST_SEQ = copy_templt_st_seq
            copy_isf_templt_st_space.MODEL_SEQ = copy_model_seq
            for copy_db_line in copy_db_line_list:
                sf_dao.insert_isf_templt_st_space(copy_isf_templt_st_space, db_line=copy_db_line)
            logger.info('sensor_copy.copy_isf_2d_model : insert ISF_TEMPLT_ST_SPACE completed. '
                         'templt_st_seq={TEMPLT_ST_SEQ}'.format(TEMPLT_ST_SEQ=copy_templt_st_seq))
        org_isf_templt_st_algrth = sf_dao.get_org_isf_templt_st_algrth(org_templt_st_algrth_seq, db_line=org_db_line)
        algrth_sensor_name = org_isf_templt_st_algrth.ALGRTH_SENSOR_NAME
        org_isf_rstep_norm_config_list = sf_dao.get_isf_rstep_norm_config(org_templt_st_seq, algrth_sensor_name, db_line=org_db_line)
        if org_isf_rstep_norm_config_list is not None and len(org_isf_rstep_norm_config_list) > 0:
            copy_isf_rstep_norm_config_list = sf_dao.get_isf_rstep_norm_config(copy_templt_st_seq, algrth_sensor_name, db_line=org_db_line)
            if copy_isf_rstep_norm_config_list is not None and len(copy_isf_rstep_norm_config_list) > 0:
                logger.info('sensor_copy.copy_isf_2d_model : already exists ISF RSTEP NORM Config. '
                             'templt_st_seq={TEMPLT_ST_SEQ}, algrth_sensor_name={ALGRTH_SENSOR_NAME}'.format(TEMPLT_ST_SEQ=copy_templt_st_seq, ALGRTH_SENSOR_NAME=algrth_sensor_name))
            else:
                copy_isf_rstep_norm_config_list = copy.deepcopy(org_isf_rstep_norm_config_list)
                for copy_isf_rstep_norm_config in copy_isf_rstep_norm_config_list:
                    copy_isf_rstep_norm_config.TEMPLT_ST_SEQ = copy_templt_st_seq
                for copy_db_line in copy_db_line_list:
                    sf_dao.insert_isf_rstep_norm_config_list(copy_isf_rstep_norm_config_list, db_line=copy_db_line)
                logger.info('sensor_copy.copy_isf_2d_model : insert ISF RSTEP NORM Config completed. '
                            'templt_st_seq={TEMPLT_ST_SEQ}, algrth_sensor_name={ALGRTH_SENSOR_NAME}'.format(TEMPLT_ST_SEQ=copy_templt_st_seq, ALGRTH_SENSOR_NAME=algrth_sensor_name))
    return copy_isf_model_list
if __name__ == '__main__':
    print('test!!')
    org_tmp_seq = 13964
    copy_tmp_seq = 13969
    isf_sensor_copy_result_list = execute_isf_sensor_copy(org_tmp_seq, copy_tmp_seq)
    mass_yn = 'Y'
    start_tmstp = '2024-08-10 00:00:00'
    end_tmstp = '2024-09-10 00:00:00'
    if mass_yn == 'Y' and isf_sensor_copy_result_list is not None and len(isf_sensor_copy_result_list) > 0:
        register_isf_mass_job(org_tmp_seq, copy_tmp_seq, isf_sensor_copy_result_list, start_tmstp, end_tmstp)