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

def apply_lot_mapping(hw_motion_hist_df, robot_motion_hist_df, carr_id, tkin_time=None, tkout_time=None):
    def _case3_labeling(df):
        tkin_dt = pd.to_datetime(tkin_time) if tkin_time is not None else None
        tkout_dt = pd.to_datetime(tkout_time) if tkout_time is not None else None
        robot_start = pd.to_datetime(robot_motion_hist_df['starttime_rev'].min())
        robot_end = pd.to_datetime(robot_motion_hist_df['endtime_rev'].max())
        
        if tkin_dt is not None and hasattr(tkin_dt, "tz_localize"):
            tkin_dt = tkin_dt.tz_localize(None)
        if tkout_dt is not None and hasattr(tkout_dt, "tz_localize"):
            tkout_dt = tkout_dt.tz_localize(None)    
        if robot_start is not None and hasattr(robot_start, "tz_localize"):
            robot_start = robot_start.tz_localize(None)
        if robot_end is not None and hasattr(robot_end, "tz_localize"):
            robot_end = robot_end.tz_localize(None)    
        
        # 기존 LOT 시작 시간 계산
        lot_start_time = tkin_dt
        
        # gab 계산 및 적용
        if robot_end is not None and tkout_dt is not None:
            gab = robot_end - tkout_dt
            lot_start_time = lot_start_time + gab - pd.DateOffset(minutes=2)

        lot_end_time = robot_end + pd.DateOffset(minutes=2)

        mask = (df['starttime_rev'] >= lot_start_time) & (df['starttime_rev'] <= lot_end_time)
        
        df.loc[mask, 'material_id'] = carr_id
        return df


    def _case2_labeling(df):
        # pass
        return df

    hw_motion_hist_df = hw_motion_hist_df.copy()

    # case3: material_id가 모두 'EMPTY'인 경우
    if (hw_motion_hist_df['material_id'] == 'EMPTY').all():
        hw_motion_hist_df = _case3_labeling(hw_motion_hist_df)
    else:
        # case2: READID state에 material_id가 있는 경우
        hw_motion_hist_df = _case2_labeling(hw_motion_hist_df)
    
    return hw_motion_hist_df

def mars_time_robot(step_seq, eqp_id, lot_id, wafer_id, src_var, dst_var, time_var):
    try:
        # 1. 전처리 작업
        root_lot_id, tkin, tkout, line_name, start_date, end_date = get_preprocessing_info(step_seq, eqp_id, lot_id, wafer_id)

        # 캐시에 조회
        cache_key = f"ROBOT_MOTION|{line_name}|{eqp_id}|{lot_id}|{step_seq}|{start_date}|{end_date}"
        robot_motion_hist_df = None
        
        # 2. Redis에서 데이터 조회
        robot_motion_hist_df, ttl = redis_cache.load_dataframe_from_redis(cache_key)
        if robot_motion_hist_df is None or ttl is None:
            logger.info(f"No robot motion data in cache (key={cache_key})")
            
            # 3. 캐시에 없으면 bigdata조회
            robot_motion_hist_df = bigdataquery_dao.get_eqp_robot_motion_history(line_name, eqp_id, lot_id, step_seq, start_date, end_date)
            
            # 4. 
            robot_motion_hist_df['wafer_id'] = robot_motion_hist_df['materialid'].apply(process_wafer_id)
            
            # 5. starttime 기준으로 정렬, 인덱스 초기화
            robot_motion_hist_df = robot_motion_hist_df.sort_values(by=['starttime'])
            robot_motion_hist_df = robot_motion_hist_df.reset_index(drop=True)

            # 6. 
            if robot_motion_hist_df is None or robot_motion_hist_df.empty:
                logger.error('robot_motion_hist_df is empty.')
                return None                
            else:
                # 7. 
                redis_cache.save_dataframe_to_redis(cache_key, robot_motion_hist_df)                
        else:
            logger.info(f"Found robot motion data in cache (key={cache_key}, ttl={ttl})")
        
        ## 8. wafer, src, dst 로 필터
        filtered_robot_motion_df = robot_motion_hist_df[robot_motion_hist_df['wafer_id'] == wafer_id]
        
        if filtered_robot_motion_df.empty:
            wafer_id_int = int(wafer_id)
            filtered_robot_motion_df = robot_motion_hist_df[robot_motion_hist_df['wafer_id'] == wafer_id_int]
            
        filtered_robot_motion_df = filtered_robot_motion_df[(filtered_robot_motion_df['srcmoduletype'] == src_var) & (filtered_robot_motion_df['dstmoduletype'] == dst_var)].reset_index(drop=True)

        ## 결과 없으면 None 리턴
        if filtered_robot_motion_df.empty:
            logger.error('filtered_robot_motion_df is empty.')
            return None

        ## 9. src || dst 가 VTM 이고 state 가 EXTEND, RETRACT 쌍인 경우 starttime = EXTEND // entime = RETRACT 로 가져 옴
        if (src_var == 'VTM' or dst_var == 'VTM') and 'EXTEND' in filtered_robot_motion_df['state'].tolist() and 'RETRACT' in filtered_robot_motion_df['state'].tolist():
            if time_var == 'START_TIME':
                result_list = [start_time.tz_localize(tz=None).to_pydatetime() for start_time in filtered_robot_motion_df[filtered_robot_motion_df['state'] == 'EXTEND']['starttime_rev'].tolist()]
            if time_var == 'END_TIME':
                result_list = [end_time.tz_localize(tz=None).to_pydatetime() for end_time in filtered_robot_motion_df[filtered_robot_motion_df['state'] == 'RETRACT']['endtime_rev'].tolist()]
            if time_var == 'PROCESS_TIME':
                start_time_list = [start_time.tz_localize(tz=None).to_pydatetime() for start_time in filtered_robot_motion_df[filtered_robot_motion_df['state'] == 'EXTEND']['starttime_rev'].tolist()]
                end_time_list = [end_time.tz_localize(tz=None).to_pydatetime() for end_time in filtered_robot_motion_df[filtered_robot_motion_df['state'] == 'RETRACT']['endtime_rev'].tolist()]
                result_list = [(end_time - start_time).total_seconds() for start_time, end_time in zip(start_time_list, end_time_list)]

        ## 10. 위 케이스 아닌 경우는 src, dst 에 해당하는 time 값 전부 리스트로 리턴
        else:
            if time_var == 'START_TIME':
                result_list = [start_time.tz_localize(tz=None).to_pydatetime() for start_time in filtered_robot_motion_df['starttime_rev'].tolist()]
            if time_var == 'END_TIME':
                result_list = [end_time.tz_localize(tz=None).to_pydatetime() for end_time in filtered_robot_motion_df['endtime_rev'].tolist()]
            if time_var == 'PROCESS_TIME':
                start_time_list = [start_time.tz_localize(tz=None).to_pydatetime() for start_time in filtered_robot_motion_df['starttime_rev'].tolist()]
                end_time_list = [end_time.tz_localize(tz=None).to_pydatetime() for end_time in filtered_robot_motion_df['endtime_rev'].tolist()]
                result_list = [(end_time - start_time).total_seconds() for start_time, end_time in zip(start_time_list, end_time_list)]

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
        
        # 3. Redis에서 데이터 조회
        robot_motion_hist_df, ttl = redis_cache.load_dataframe_from_redis(cache_key)
        
        if robot_motion_hist_df is None or ttl is None:
            logger.info(f"No robot motion data in cache (key={cache_key})")
            
            # 4. 캐시에 없으면 bigdata조회
            robot_motion_hist_df = bigdataquery_dao.get_eqp_robot_motion_history(line_name, eqp_id, lot_id, step_seq, start_date, end_date)            
            robot_motion_hist_df['wafer_id'] = robot_motion_hist_df['materialid'].apply(process_wafer_id)            
            robot_motion_hist_df = robot_motion_hist_df.sort_values(by=['starttime_rev'])
            robot_motion_hist_df = robot_motion_hist_df.reset_index(drop=True)
            
            if robot_motion_hist_df is None or robot_motion_hist_df.empty:
                logger.error('robot_motion_hist_df is empty.')
                return None                
            else:
                 # 6. 
                redis_cache.save_dataframe_to_redis(cache_key, robot_motion_hist_df)
        else:
            logger.info(f"found robot motion data in cache (key={cache_key})")
        
        # 7. hw검색용 정보 전처리
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

        # 8. hw_motion_hist_df redis / 캐시에 조회
        hw_cache_key = f"HW_MOTION|{line_name}|{eqp_id}|{src_module_id}|{work_var}|{start_date}|{end_date}"
        hw_motion_hist_df = None

        # 8-1. Redis에서 데이터 조회
        hw_motion_hist_df, ttl = redis_cache.load_dataframe_from_redis(hw_cache_key)
        
        if hw_motion_hist_df is None or ttl is None:
            logger.info(f"No hw motion data in cache (key={hw_cache_key})")
            
            # 9. 캐시에 없으면 bigdata조회
            hw_motion_hist_df = bigdataquery_dao.get_eqp_hw_motion_history(line_name, eqp_id, src_module_id, work_var, start_date, end_date)
            
            if hw_motion_hist_df is None or hw_motion_hist_df.empty:
                logger.error('hw_motion_hist_df is empty.')
                return None
            else:
                # 10.
                redis_cache.save_dataframe_to_redis(hw_cache_key, hw_motion_hist_df)
                # starttime 기준으로 정렬, 인덱스 초기화
                hw_motion_hist_df = hw_motion_hist_df.sort_values(by=['start_time'])
                hw_motion_hist_df = hw_motion_hist_df.reset_index(drop=True)                              
        else:
            logger.info(f"Found hw motion data in cache (key={hw_cache_key}, ttl={ttl})")
            
            # starttime 기준으로 정렬, 인덱스 초기화
            hw_motion_hist_df = hw_motion_hist_df.sort_values(by=['starttime_rev'])
            hw_motion_hist_df = hw_motion_hist_df.reset_index(drop=True) 

        # 11. hw정보 처리 결과가 있으면 return result_list
        ## 11.1. 설정된 state 로 material_id 가 존재 하는 경우
        if work_var == "LOADPORT":
            filtered_hw_motion_hist_df = hw_motion_hist_df[(hw_motion_hist_df['material_id'] == tkin.CARR_ID) & (hw_motion_hist_df['state'] == state_var)]
        else:
            # 로드포트가 아닐때는
            # hw_motion_hist_df['material_id'] 앞부분을 짤라서 'new_lot_id' 칼럼으로 만든후  인자값 lot_id와 비교하고 , state_var = 'DECHUCK' 값으로 필터링한게 최종 값이 된다. 

            
            hw_motion_hist_df['wafer_id'] = hw_motion_hist_df['material_id'].apply(process_wafer_id)
            filtered_hw_motion_hist_df = hw_motion_hist_df[((hw_motion_hist_df['wafer_id'] == wafer_id) | hw_motion_hist_df['wafer_id'] == int(wafer_id))  & (hw_motion_hist_df['state'] == state_var)]
            
            
        ## 11.2. 설정된 state 로 material_id 가 없는 경우 (material_id = EMPTY) and # Case 3 매핑 적용 (모든 material_id가 'EMPTY'인 경우)
        if filtered_hw_motion_hist_df.empty and (hw_motion_hist_df['material_id'] == 'EMPTY').all():
            # _case3_labeling을 apply_lot_mapping의 내부에서 활용
            hw_motion_hist_df = apply_lot_mapping(hw_motion_hist_df, robot_motion_hist_df, tkin.CARR_ID, tkin.LOT_TRANSN_TMSTP)

            # case3 labeling이후 다시 결과를 가져옴
            filtered_hw_motion_hist_df = hw_motion_hist_df[(hw_motion_hist_df['material_id'] == tkin.CARR_ID) & (hw_motion_hist_df['state'] == state_var)]
            
            
        elif filtered_hw_motion_hist_df.empty and not (hw_motion_hist_df['material_id'] == 'EMPTY').all():
            # else 이하 로직 (기존 11.2) 적용
            idx_list = hw_motion_hist_df[(hw_motion_hist_df['state'] == 'READID') & (hw_motion_hist_df['material_id'] != 'EMPTY')].index.tolist()
            cur_idx_series = hw_motion_hist_df[(hw_motion_hist_df['state'] == 'READID') & (hw_motion_hist_df['material_id'] == tkin.CARR_ID)].index
            if len(idx_list) == 0 or len(cur_idx_series) == 0:
                logger.error('No valid READID found for material_id')
                return None
            cur_idx = cur_idx_series[0]
            cur_start_time = hw_motion_hist_df.iloc[cur_idx].start_time

            ## 11.2_1. 현재 READID ~ 다음 READID 사이에서 검색
            if state_var in next_state:
                try:
                    next_idx = idx_list[idx_list.index(cur_idx) + 1]
                    next_start_time = hw_motion_hist_df.iloc[next_idx].start_time
                    filtered_hw_motion_hist_df = hw_motion_hist_df[(hw_motion_hist_df['starttime_rev'] > cur_start_time) & 
                                                                 (hw_motion_hist_df['starttime_rev'] < next_start_time) & 
                                                                 (hw_motion_hist_df['state'] == state_var)]
                except (ValueError, IndexError):
                    logger.error('No next READID found for state')
                    return None

            ## 11.2_2. 이전 READID ~ 현재 READID 사이에서 검색
            elif state_var in prev_state:
                try:
                    prev_idx = idx_list[idx_list.index(cur_idx) - 1]
                    prev_start_time = hw_motion_hist_df.iloc[prev_idx].start_time
                    filtered_hw_motion_hist_df = hw_motion_hist_df[(hw_motion_hist_df['starttime_rev'] > prev_start_time) & 
                                                                 (hw_motion_hist_df['starttime_rev'] < cur_start_time) & 
                                                                 (hw_motion_hist_df['state'] == state_var)]
                except (ValueError, IndexError):
                    logger.error('No previous READID found for state')
                    return None

            ## 11.2_3. 이전 READID ~ 다음 READID 사이에서 검색
            else:
                try:
                    next_idx = idx_list[idx_list.index(cur_idx) + 1]
                    next_start_time = hw_motion_hist_df.iloc[next_idx].start_time
                    prev_idx = idx_list[idx_list.index(cur_idx) - 1]
                    prev_start_time = hw_motion_hist_df.iloc[prev_idx].start_time
                    filtered_hw_motion_hist_df = hw_motion_hist_df[(hw_motion_hist_df['starttime_rev'] > prev_start_time) & 
                                                                 (hw_motion_hist_df['starttime_rev'] < next_start_time) & 
                                                                 (hw_motion_hist_df['state'] == state_var)]
                except (ValueError, IndexError):
                    logger.error('No previous or next READID found for state')
                    return None

        ## 결과 없으면 None 리턴
        if filtered_hw_motion_hist_df.empty:
            logger.error('filtered_hw_motion_hist_df is empty.')
            return None
        
        # 12. 결과 있으면 time_var 설정대로 결과 생성
        if time_var == 'START_TIME':
            result_list = [start_time.tz_localize(tz=None).to_pydatetime() for start_time in filtered_hw_motion_hist_df['starttime_rev'].tolist()]
        elif time_var == 'END_TIME':
            result_list = [end_time.tz_localize(tz=None).to_pydatetime() for end_time in filtered_hw_motion_hist_df['endtime_rev'].tolist()]
        elif time_var == 'PROCESS_TIME':
            start_time_list = [start_time.tz_localize(tz=None).to_pydatetime() for start_time in filtered_hw_motion_hist_df['starttime_rev'].tolist()]
            end_time_list = [end_time.tz_localize(tz=None).to_pydatetime() for end_time in filtered_hw_motion_hist_df['endtime_rev'].tolist()]
            result_list = [(end_time - start_time).total_seconds() for start_time, end_time in zip(start_time_list, end_time_list)]
        else:
            logger.error(f'Invalid time_var: {time_var}')
            return None

        return result_list

    except Exception as e:
        logger.exception(f"Error in mars_time_hw: {str(e)}")
        return None

def mars_time_process(step_seq, eqp_id, lot_id, wafer_id, time_var):
    try:     
        # 1. 전처리 작업
        root_lot_id, tkin, tkout, line_name, start_date, end_date = get_preprocessing_info(step_seq, eqp_id, lot_id, wafer_id)

        # 2. Redis key 생성
        cache_key = f"PRPC_MOTION|{line_name}|{eqp_id}|{lot_id}|{step_seq}|{start_date}|{end_date}"
        process_hist_df = None
        
        # 3. Redis에서 데이터 조회
        process_hist_df, ttl = redis_cache.load_dataframe_from_redis(cache_key)
        
        if process_hist_df is None or ttl is None:
            logger.info(f"No process_hist_df data in cache (key={cache_key})")
            
            # 4. 캐시에 없으면 bigdata조회
            process_hist_df = bigdataquery_dao.get_eqp_hw_process_history(line_name, eqp_id, lot_id, step_seq, start_date, end_date)            
            process_hist_df['wafer_id'] = process_hist_df['materialid'].apply(process_wafer_id)            
            process_hist_df = process_hist_df.sort_values(by=['starttime_rev'])
            process_hist_df = process_hist_df.reset_index(drop=True)
            
            if process_hist_df is None or process_hist_df.empty:
                logger.error('process_hist_df is empty.')
                return None                
            else:
                redis_cache.save_dataframe_to_redis(cache_key, process_hist_df)
        else:
            logger.info(f"found process_hist_df data in cache (key={cache_key})")
        
        # 5. hw검색용 정보 전처리 
        filtered_df = process_hist_df[process_hist_df['wafer_id'] == wafer_id]
        
        if filtered_df.empty:
            wafer_id_int = int(wafer_id)
            filtered_df = process_hist_df[process_hist_df['wafer_id'] == wafer_id_int]
                
        # 6. 'moduleid'별로 첫 행과 마지막 행만 남기는 필터링
        if not filtered_df.empty:
            first_rows = filtered_df.groupby('module_id', as_index=False).first()
            last_rows = filtered_df.groupby('module_id', as_index=False).last()
            filtered_process_hist_df = pd.concat([first_rows, last_rows]).drop_duplicates().reset_index(drop=True)

        ## 결과 없으면 None 리턴
        if filtered_process_hist_df.empty:
            logger.error('filtered_process_hist_df is empty.')
            return None

        # 12. 결과 있으면 time_var 설정대로 결과 생성
        result_list = []
        grouped = filtered_hw_motion_hist_df.groupby('moduleid')

        # 각 그룹을 starttime_rev로 오름차순 정렬
        groups = {name: group.sort_values(by='starttime_rev') for name, group in grouped}
        
        if time_var == 'START_TIME':
            # moduleid별 starttime_rev 최소값 리스트
            result_list = [group['starttime_rev'].min().tz_localize(tz=None).to_pydatetime() for name, group in grouped]
        elif time_var == 'END_TIME':
            # moduleid별 endtime_rev 최대값 리스트
            result_list = [group['endtime_rev'].max().tz_localize(tz=None).to_pydatetime() for name, group in grouped]
        elif time_var == 'PROCESS_TIME':
            # moduleid별 (endtime_rev 최대값 - starttime_rev 최소값).total_seconds() 리스트
            for name, group in grouped:
                start_time = group['starttime_rev'].min().tz_localize(tz=None)
                end_time = group['endtime_rev'].max().tz_localize(tz=None)
                result_list.append((end_time - start_time).total_seconds())
        else:
            logger.error(f'Invalid time_var: {time_var}')
            return None
        
        return result_list

    except Exception as e:
        logger.exception(f"Error in process_hist_df: {str(e)}")
        return None
        
if __name__ == "__main__":
    logger.info("============= MARS TEST  ===============")

    ## hw_motio_history : PROCESS_TIME 선택시 정수로 나오는부분 체크바람 (robot_motio_history는 소수점 까지 잘나옴)

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

    # test mars_time_hw_process
    hw_result = mars_time_process(step_seq, eqp_id, lot_id, wafer_id, time_var)
    logger.info(f"HW process result: {hw_result}") 


##[MARS_TIME_P_IDLE]함수 신규생성해야 하는데 rule은 다음과 같다
## 처리순서
Bigdataquery를 조회한 결과를 fab_df로 받는다 그 칼럼리스트 = [equipmentid,moduleid,workgroup,state,starttime_rev,endtime_rev,materialid,recipename,if_step_seq,if_lot_id,if_tkin_date]이다
    0. fab_df(원본)을  starttime_rev 오름차순 정렬한다
    1. fab_df을 materialid,if_step_seq,if_lot_id 로 전달받은 param값으로 필터링한다
    2. 1번결과에서 moduleid의 distinct값을 구한다 ex) moduleid_distinct = ['ch4','ch2']
    3. fab_df(원본) 값에서 moduleid == moduleid_distinct[0] 로 필터링한다
    4. 3번결과에서 materialid,if_step_seq,if_lot_id 로 전달받은 param값으로 구분했을때, 그때의 첫번째행의 starttime_rev값과  ,
        그 이전행의 (materialid가 다른행) endtime_rev 값과의 시간 차이를 구해 result 리스트에 넣는다 (단위는 tz_localize(tz=None))
    5. moduleid_distinct리스트가 1개 이상이면 3,4번을 반복문에 의해 수행하여 result리스트에 생성해서 최종 반환한다
    6. 만약 4번 수행시 이전행이 존재하지 않는다면 -1를 result리스트에 넣는다



    



