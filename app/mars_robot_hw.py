from dao import vm_dao, bigdataquery_dao
from app import app_common_function
from app import redis_cache
import logging
from datetime import timedelta
import pandas as pd
import json
import time

logger = logging.getLogger(__name__)

def get_preprocessing_info(step_seq, eqp_id, lot_id, wafer_id):
    """
    공통 전처리 정보를 조회하는 함수
    
    Args:
        step_seq (str): 스텝 시퀀스
        eqp_id (str): 장비 ID
        lot_id (str): 랏 ID
        wafer_id (str): 웨이퍼 ID
        
    Returns:
        tuple: (root_lot_id, tkin, tkout, line_name, start_date, end_date)
    """
    # 현재 랏의 ROOT_LOT_ID 생성
    root_lot_id = app_common_function.generate_root_lot_id(lot_id)

    # 현재 랏의 TKIN, TKOUT 조회
    tkin = vm_dao.get_lot_tkin_info(root_lot_id, step_seq, int(wafer_id))
    tkout = vm_dao.get_lot_tkout_info(lot_id, step_seq, eqp_id)

    # robot_motion, hw_motion 에서 사용하는 line_name 은 P1 과 같은 형태이므로 VM DB 에서 가져오는 LINE_NAME 에서 마지막 L 을 제거하고 사용
    line_name = vm_dao.get_line_name(tkout.LINE_ID)
    if line_name[-1] == 'L':
        line_name = line_name[:-1]

    # robot_motion, hw_motion 시간 조회 범위는 TKIN -1 ~ TKOUT +1
    start_date = (tkin.LOT_TRANSN_TMSTP + timedelta(days=-1)).strftime("%Y-%m-%d")
    end_date = (tkout.LOT_TRANSN_TMSTP + timedelta(days=1)).strftime("%Y-%m-%d")
    
    return root_lot_id, tkin, tkout, line_name, start_date, end_date

def process_wafer_id(material_id):
    if ':' in material_id:
        parts = material_id.split(':')
        num = parts[-1].zfill(2)
        return num
    elif '_' in material_id:
        parts = material_id.split('_')
        num = parts[-1].zfill(2)
        return num
    elif '.' in material_id:
        parts = material_id.split('.')
        num = ''.join(filter(str.isdigit, parts[-1])).zfill(2)
        return num
    elif ' ' in material_id:
        parts = material_id.split()
        num = ''.join(filter(str.isdigit, parts[-1])).zfill(2)
        return num  
    elif any(prefix in material_id for prefix in ['WA','WB','WC']):
        import re
        num = re.sub(r'WA|WB|WC', '' , material_id).zfill(2)
        return num 
        
    return material_id


def mars_time_robot(step_seq, eqp_id, lot_id, wafer_id, src_var, dst_var, time_var):
    try:
        # 1. 전처리 작업
        root_lot_id, tkin, tkout, line_name, start_date, end_date = get_preprocessing_info(step_seq, eqp_id, lot_id, wafer_id)

        # 2. 캐시에 조회
        cache_key = f"ROBOT_MOTION|{line_name}|{eqp_id}|{lot_id}|{step_seq}|{start_date}|{end_date}"
        robot_motion_hist_df = None
        
        # Redis에서 데이터 조회
        robot_motion_hist_df, ttl = redis_cache.load_dataframe_from_redis(cache_key)
        if robot_motion_hist_df is None or ttl is None:
            logger.info(f"No robot motion data in cache (key={cache_key})")
            
            # 3. 캐시에 없으면 bigdata조회
            robot_motion_hist_df = bigdataquery_dao.get_eqp_robot_motion_history(line_name, eqp_id, lot_id, step_seq, start_date, end_date)
            if robot_motion_hist_df is not None and not robot_motion_hist_df.empty:
                robot_motion_hist_df['wafer_id'] = robot_motion_hist_df['materialid'].apply(process_wafer_id)
                # starttime 기준으로 정렬, 인덱스 초기화
                robot_motion_hist_df = robot_motion_hist_df.sort_values(by=['starttime'])
                robot_motion_hist_df = robot_motion_hist_df.reset_index(drop=True)
                redis_cache.save_dataframe_to_redis(cache_key, robot_motion_hist_df)
            else:
                logger.error('robot_motion_hist_df is empty.')
                return None
        else:
            logger.info(f"Found robot motion data in cache (key={cache_key}, ttl={ttl})")
        
        ## wafer, src, dst 로 필터
        filtered_robot_motion_df = robot_motion_hist_df[robot_motion_hist_df['wafer_id'] == wafer_id]
        if filtered_robot_motion_df.empty:
            wafer_id_int = int(wafer_id)
            filtered_robot_motion_df = robot_motion_hist_df[robot_motion_hist_df['wafer_id'] == wafer_id_int]
            
        filtered_robot_motion_df = filtered_robot_motion_df[(filtered_robot_motion_df['srcmoduletype'] == src_var) & (filtered_robot_motion_df['dstmoduletype'] == dst_var)].reset_index(drop=True)

        ## 결과 없으면 None 리턴
        if filtered_robot_motion_df.empty:
            logger.error('filtered_robot_motion_df is empty.')
            return None

        ## src || dst 가 VTM 이고 state 가 EXTEND, RETRACT 쌍인 경우 starttime = EXTEND // entime = RETRACT 로 가져 옴
        if (src_var == 'VTM' or dst_var == 'VTM') and 'EXTEND' in filtered_robot_motion_df['state'].tolist() and 'RETRACT' in filtered_robot_motion_df['state'].tolist():
            if time_var == 'START_TIME':
                result_list = [start_time.to_pydatetime() for start_time in filtered_robot_motion_df[filtered_robot_motion_df['state'] == 'EXTEND']['starttime'].tolist()]
            elif time_var == 'END_TIME':
                result_list = [end_time.to_pydatetime() for end_time in filtered_robot_motion_df[filtered_robot_motion_df['state'] == 'RETRACT']['endtime'].tolist()]
            elif time_var == 'PROCESS_TIME':
                start_time_list = [start_time.to_pydatetime() for start_time in filtered_robot_motion_df[filtered_robot_motion_df['state'] == 'EXTEND']['starttime'].tolist()]
                end_time_list = [end_time.to_pydatetime() for end_time in filtered_robot_motion_df[filtered_robot_motion_df['state'] == 'RETRACT']['endtime'].tolist()]
                result_list = [(end_time - start_time).seconds for start_time, end_time in zip(start_time_list, end_time_list)]
            else:
                logger.error(f'Invalid time_var: {time_var}')
                return None

        ## 위 케이스 아닌 경우는 src, dst 에 해당하는 time 값 전부 리스트로 리턴
        else:
            if time_var == 'START_TIME':
                result_list = [start_time.to_pydatetime() for start_time in filtered_robot_motion_df['starttime'].tolist()]
            elif time_var == 'END_TIME':
                result_list = [end_time.to_pydatetime() for end_time in filtered_robot_motion_df['endtime'].tolist()]
            elif time_var == 'PROCESS_TIME':
                start_time_list = [start_time.to_pydatetime() for start_time in filtered_robot_motion_df['starttime'].tolist()]
                end_time_list = [end_time.to_pydatetime() for end_time in filtered_robot_motion_df['endtime'].tolist()]
                result_list = [(end_time - start_time).seconds for start_time, end_time in zip(start_time_list, end_time_list)]
            else:
                logger.error(f'Invalid time_var: {time_var}')
                return None

        return result_list

    except Exception as e:
        logger.exception(f"Error in mars_time_robot: {str(e)}")
        return None

def mars_time_hw(step_seq, eqp_id, lot_id, wafer_id, work_var, state_var, time_var):
    try:
        # 1. 전처리 작업
        root_lot_id, tkin, tkout, line_name, start_date, end_date = get_preprocessing_info(step_seq, eqp_id, lot_id, wafer_id)

        # 2. robot_motion_hist_df redis / 캐시에 조회
        cache_key = f"ROBOT_MOTION|{line_name}|{eqp_id}|{lot_id}|{step_seq}|{start_date}|{end_date}"
        robot_motion_hist_df = None
        
        # Redis에서 데이터 조회
        robot_motion_hist_df, ttl = redis_cache.load_dataframe_from_redis(cache_key)
        if robot_motion_hist_df is None or ttl is None:
            logger.info(f"No robot motion data in cache (key={cache_key})")
            return None
        
        # 3. hw검색용 정보 전처리
        # wafer, src, dst 로 필터
        filtered_df = robot_motion_hist_df[robot_motion_hist_df['wafer_id'] == wafer_id]
        if filtered_df.empty:
            wafer_id_int = int(wafer_id)
            filtered_df = robot_motion_hist_df[robot_motion_hist_df['wafer_id'] == wafer_id_int]

        
        filtered_df = filtered_df[(filtered_df['srcmoduletype'] == work_var) | (filtered_df['dstmoduletype'] == work_var)].reset_index(drop=True)
        src_module_id = filtered_df[filtered_df['srcmoduletype'] == work_var].iloc[0].srcmoduleid
        dst_module_id = filtered_df[filtered_df['dstmoduletype'] == work_var].iloc[0].dstmoduleid

        ## src_module_id 와 dst_module_id 가 다르면 None 리턴
        if src_module_id != dst_module_id:
            logger.error('src_module_id not same as dst_module_id.')

        ## 내 랏 READID 기준으로 나중에 오는 상태 값, 이전에 오는 상태 값 목록
        next_state = ['LPFORWARD', 'FOUPDOOROPEN', 'MAPPING', 'FOUPDOORCLOSE', 'LPDECHUCK']
        prev_state = ['PURGE_FRONT', 'PURGE_REAR', 'LPCHUCK']

        # 4. hw_motion_hist_df redis / 캐시에 조회
        hw_cache_key = f"HW_MOTION|{line_name}|{eqp_id}|{src_module_id}|{work_var}|{start_date}|{end_date}"
        hw_motion_hist_df = None

        # Redis에서 데이터 조회
        hw_motion_hist_df, ttl = redis_cache.load_dataframe_from_redis(hw_cache_key)
        if hw_motion_hist_df is None or ttl is None:
            logger.info(f"No hw motion data in cache (key={hw_cache_key})")
            
            # 5. 캐시에 없으면 bigdata조회
            hw_motion_hist_df = bigdataquery_dao.get_eqp_hw_motion_history(line_name, eqp_id, src_module_id, work_var, start_date, end_date)
            if hw_motion_hist_df is not None and not hw_motion_hist_df.empty:
                # starttime 기준으로 정렬, 인덱스 초기화
                hw_motion_hist_df = hw_motion_hist_df.sort_values(by=['start_time'])
                hw_motion_hist_df = hw_motion_hist_df.reset_index(drop=True)
                redis_cache.save_dataframe_to_redis(hw_cache_key, hw_motion_hist_df)
            else:
                logger.error('hw_motion_hist_df is empty.')
                return None
        else:
            logger.info(f"Found hw motion data in cache (key={hw_cache_key}, ttl={ttl})")
        
        # 7. hw정보 처리 결과가 있으면 return result_list
        ## 7.1. 설정된 state 로 material_id 가 존재 하는 경우
        filtered_hw_motion_hist_df = hw_motion_hist_df[(hw_motion_hist_df['material_id'] == tkin.CARR_ID) & (hw_motion_hist_df['state'] == state_var)]

        ## 7.2. 설정된 state 로 material_id 가 없는 경우 (material_id = EMPTY)
        if filtered_hw_motion_hist_df.empty:
            ## 없으면 state == READID 기준 이전 랏, 내 랏, 다음 랏 위치 찾음
            idx_list = hw_motion_hist_df[(hw_motion_hist_df['state'] == 'READID') & (hw_motion_hist_df['material_id'] != 'EMPTY')].index.tolist()
            
            if not idx_list:
                logger.error('No READID state found in hw_motion_hist_df')
                return None

            cur_idx = hw_motion_hist_df[(hw_motion_hist_df['state'] == 'READID') & (hw_motion_hist_df['material_id'] == tkin.CARR_ID)].index[0]
            cur_start_time = hw_motion_hist_df.iloc[cur_idx].start_time

            ## 7.2_1. 현재 READID ~ 다음 READID 사이에서 검색
            if state_var in next_state:
                if cur_idx + 1 >= len(idx_list):
                    logger.error('No next READID found')
                    return None
                next_idx = idx_list[idx_list.index(cur_idx) + 1]
                next_start_time = hw_motion_hist_df.iloc[next_idx].start_time

                filtered_hw_motion_hist_df = hw_motion_hist_df[(hw_motion_hist_df['start_time'] > cur_start_time) & 
                                                             (hw_motion_hist_df['start_time'] < next_start_time) & 
                                                             (hw_motion_hist_df['state'] == state_var)]

            ## 7.2_2. 이전 READID ~ 현재 READID 사이에서 검색
            elif state_var in prev_state:
                if cur_idx == 0:
                    logger.error('No previous READID found')
                    return None
                prev_idx = idx_list[idx_list.index(cur_idx) - 1]
                prev_start_time = hw_motion_hist_df.iloc[prev_idx].start_time

                filtered_hw_motion_hist_df = hw_motion_hist_df[(hw_motion_hist_df['start_time'] > prev_start_time) & 
                                                             (hw_motion_hist_df['start_time'] < cur_start_time) & 
                                                             (hw_motion_hist_df['state'] == state_var)]

            ## 7.2_3. 이전 READID ~ 다음 READID 사이에서 검색
            else:
                if cur_idx == 0 or cur_idx + 1 >= len(idx_list):
                    logger.error('No previous or next READID found')
                    return None
                next_idx = idx_list[idx_list.index(cur_idx) + 1]
                next_start_time = hw_motion_hist_df.iloc[next_idx].start_time
                prev_idx = idx_list[idx_list.index(cur_idx) - 1]
                prev_start_time = hw_motion_hist_df.iloc[prev_idx].start_time

                filtered_hw_motion_hist_df = hw_motion_hist_df[(hw_motion_hist_df['start_time'] > prev_start_time) & 
                                                             (hw_motion_hist_df['start_time'] < next_start_time) & 
                                                             (hw_motion_hist_df['state'] == state_var)]

        ## 결과 없으면 None 리턴
        if filtered_hw_motion_hist_df.empty:
            logger.error('filtered_hw_motion_hist_df is empty.')
            return None

        # 결과 있으면 time_var 설정대로 결과 생성
        if time_var == 'START_TIME':
            result_list = [start_time.to_pydatetime() for start_time in filtered_hw_motion_hist_df['start_time'].tolist()]
        elif time_var == 'END_TIME':
            result_list = [end_time.to_pydatetime() for end_time in filtered_hw_motion_hist_df['end_time'].tolist()]
        elif time_var == 'PROCESS_TIME':
            start_time_list = [start_time.to_pydatetime() for start_time in filtered_hw_motion_hist_df['start_time'].tolist()]
            end_time_list = [end_time.to_pydatetime() for end_time in filtered_hw_motion_hist_df['end_time'].tolist()]
            result_list = [(end_time - start_time).seconds for start_time, end_time in zip(start_time_list, end_time_list)]
        else:
            logger.error(f'Invalid time_var: {time_var}')
            return None

        return result_list

    except Exception as e:
        logger.exception(f"Error in mars_time_hw: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("============= MARS TEST  ===============")

    ## ETCH CASE 2
    eqp_id = 'ETOP327'
    lot_id = 'PBD542.1'
    step_seq = 'CR125120'
    wafer_id = '08'

    src_var = 'LOADLOCK'
    dst_var = 'VTM'
    time_var = 'PROCESS_TIME'

    work_var = 'LOADPORT'
    state_var = 'FOUPDOOROPEN'
    time_var = 'PROCESS_TIME'

    start_time = time.time()
    
    # Test mars_time_robot
    robot_result = mars_time_robot(step_seq, eqp_id, lot_id, wafer_id, src_var, dst_var, time_var)
    logger.info(f"Robot result: {robot_result}")

    # Test mars_time_hw
    hw_result = mars_time_hw(step_seq, eqp_id, lot_id, wafer_id, work_var, state_var, time_var)
    logger.info(f"HW result: {hw_result}") 
    
    end_time = time.time()
    print(f'수행시간 : {end_time - start_time} 초 소요 ')   
    
