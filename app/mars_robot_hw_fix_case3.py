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

    # 현재 랏의 ROOT_LOT_ID 생성
    root_lot_id = app_common_function.generate_root_lot_id(lot_id)

    # 현재 랏의 TKIN, TKOUT 조회
    tkin = vm_dao.get_cur_lot_tkin_info(lot_id, step_seq, int(wafer_id))
    tkout = vm_dao.get_lot_tkout_info(lot_id, step_seq, eqp_id)

    # robot_motion, hw_motion 에서 사용하는 line_name 은 P1 과 같은 형태이므로 VM DB 에서 가져오는 LINE_NAME 에서 마지막 L 을 제거하고 사용
    # line_name = vm_dao.get_line_name(tkout.LINE_ID)
    # if line_name[-1] == 'L':
    #     line_name = line_name[:-1]

    # robot_motion, hw_motion 시간 조회 범위는 TKIN -1 ~ TKOUT +1
    start_date = (tkin.LOT_TRANSN_TMSTP + timedelta(days=-1)).strftime("%Y-%m-%d")
    end_date = (tkout.LOT_TRANSN_TMSTP + timedelta(days=1)).strftime("%Y-%m-%d")

    #target_line도 캐쉬에 넣는다
    cache_key = f"MARS_EQP_LINE|{eqp_id}"
    #mars_eqp_line_df, ttl = redis_cache.load_dataframe_from_fedis(cache_key)
    mars_eqp_line, ttl = redis_cache.load_string_from_redis(cache_key)

    if mars_eqp_line is None or ttl is None:
        target_line = bigdataquery_dao.get_targetline_by_site_and_eqp(eqp_id)
        ########################################
        if target_line is None or (isinstance(target_line, str) and target_line.strip() = =""):
            logger.info(f" target_line {target_line} is NOne . Aborting preprocessing.")
            raise RuntimeError(f" target_line {target_line} is NOne . Aborting preprocessing.")
        ########################################
        redis_cache.save_string_to_redis(cache_key, target_line)
    else:
        target_line = mars_eqp_line
    
    return root_lot_id, tkin, tkout, start_date, end_date, target_line

def process_wafer_id(material_id):
    if ':' in material_id:
        parts = material_id.split(':')
        num = parts[-1].zfill(2)
        return num
    elif '_' in material_id:
        parts = material_id.split('_')
        num = parts[-1].zfill(2)
        return num
    elif '-' in material_id:
        parts = material_id.split('-')
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

def mars_time_robot(step_seq, eqp_id, lot_id, wafer_id, src_var, dst_var, state_var, time_var):
    try:
        # 1. 전처리 작업
        root_lot_id, tkin, tkout, start_date, end_date, target_line = get_preprocessing_info(step_seq, eqp_id, lot_id, wafer_id)

        # 캐시에 조회
        cache_key = f"ROBOT_MOTION|{target_line}|{eqp_id}|{lot_id}|{step_seq}|{start_date}|{end_date}"
        robot_motion_hist_df = None
        
        # 2. Redis에서 데이터 조회
        robot_motion_hist_df, ttl = redis_cache.load_dataframe_from_redis(cache_key)
        if robot_motion_hist_df is None or ttl is None:
            logger.info(f"No robot motion data in cache (key={cache_key})")
            
            # 3. 캐시에 없으면 bigdata조회
            # robot_motion_hist_df = bigdataquery_dao.get_eqp_robot_motion_history(target_line, eqp_id, lot_id, step_seq, start_date, end_date)
            # 1015 수정
            robot_motion_hist_df = bigdataquery_dao.get_eqp_robot_motion_history_new(target_line, eqp_id, start_date, end_date, lot_id)

            # 1015 여기에 robot_motion_hist_df is None 이면 끝내는 부분 필요
            if robot_motion_hist_df is None:
                logger.info("No data")
                return None
            
            # 8월5일 추가분            
            robot_motion_hist_df = robot_motion_hist_df[ (robot_motion_hist_df['lotid'] == tkout.LOT_ID) | (robot_motion_hist_df['if_lot_id'] == tkout.LOT_ID)]
            
            # starttime_tev, endtime_rev 컬럼의 타임존 제거
            robot_motion_hist_df['starttime_rev'] = pd.to_datetime(robot_motion_hist_df['starttime_rev']).dt.tz_localize(None)
            robot_motion_hist_df['endtime_rev'] = pd.to_datetime(robot_motion_hist_df['endtime_rev']).dt.tz_localize(None)

            # tkin, tkout의 LOT_TRANSN_TMSTP에서 타임존 제거
            tkin_dt = pd.to_datetime(tkin.LOT_TRANSN_TMSTP) - pd.DateOffset(minutes=60) if tkin is not None else None
            tkout_dt = pd.to_datetime(tkout.LOT_TRANSN_TMSTP) - pd.DateOffset(minutes=60) if tkout is not None else None
            
            if hasattr(tkin_dt, "tz_localize"):
                tkin_dt = tkin_dt.tz_localize(None)
            if hasattr(tkout_dt, "tz_localize"):
                tkout_dt = tkout_dt.tz_localize(None)

            if tkin is not None and tkout is not None :
                robot_motion_hist_df = robot_motion_hist_df[
                    (tkin_dt <= robot_motion_hist_df['starttime_tev']) & (robot_motion_hist_df['endtime_rev'] <= tkout_dt)
                ]
            # 8월5일 추가분
            
            # 4. 
            robot_motion_hist_df['wafer_id'] = robot_motion_hist_df['materialid'].apply(process_wafer_id)
            
            # 5. starttime 기준으로 정렬, 인덱스 초기화 1015 starttime --> starttime_rev
            robot_motion_hist_df = robot_motion_hist_df.sort_values(by=['starttime_rev'])
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
            
        filtered_robot_motion_df = filtered_robot_motion_df[(filtered_robot_motion_df['srcmoduletype'] == src_var) 
                                                    & (filtered_robot_motion_df['dstmoduletype'] == dst_var)].reset_index(drop=True)

        ## 결과 없으면 None 리턴
        if filtered_robot_motion_df.empty:
            logger.error('filtered_robot_motion_df is empty.')
            return None

        ##신규로직시작
        if state_var == 'ALL':
            state_filtered_df = filtered_robot_motion_df
        else:
            state_filtered_df = filtered_robot_motion_df[filtered_robot_motion_df['state'] == state_var].reset_index(drop=True)
            if state_filtered_df.empty:
                logger.error('No data found for state: {state_var}')
                return None
                
        if time_var == 'START_TIME':
            result_list = [start_time.tz_localize(tz=None).to_pydatetime() for start_time in state_filtered_df['starttime_rev'].tolist()]
        if time_var == 'END_TIME':
            result_list = [end_time.tz_localize(tz=None).to_pydatetime() for end_time in state_filtered_df['endtime_rev'].tolist()]
        if time_var == 'PROCESS_TIME':
            start_time_list = [start_time.tz_localize(tz=None).to_pydatetime() for start_time in state_filtered_df['starttime_rev'].tolist()]
            end_time_list = [end_time.tz_localize(tz=None).to_pydatetime() for end_time in state_filtered_df['endtime_rev'].tolist()]
            result_list = [(end_time - start_time).total_seconds() for start_time, end_time in zip(start_time_list, end_time_list)]

        return result_list

    except Exception as e:
        logger.exception(f"Error in mars_time_robot: {str(e)}")
        return None

def mars_time_hw(step_seq, eqp_id, lot_id, wafer_id, work_var, state_var, time_var):
    try:
        # 1. 전처리 작업
        root_lot_id, tkin, tkout, start_date, end_date, target_line = get_preprocessing_info(step_seq, eqp_id, lot_id, wafer_id)

        # target_line만 검사
        if target_line is None or (isinstance(target_line, str) and not target_line.strip()):
            logger.error(f"Preprocessing failed (target_line is None or empty): (eqp_id={eqp_id}, lot_id={lot_id}, wafer_id={wafer_id}).")
            return None
            
        # 2. robot_motion_hist_df redis / 캐시에 조회
        cache_key = f"ROBOT_MOTION|{target_line}|{eqp_id}|{lot_id}|{step_seq}|{start_date}|{end_date}"
      
        # 3. Redis에서 데이터 조회
        robot_motion_hist_df, ttl = redis_cache.load_dataframe_from_redis(cache_key)
        
        if robot_motion_hist_df is None or ttl is None:
            logger.info(f"No robot motion data in cache (key={cache_key})")
            
            # 4. 캐시에 없으면 bigdata조회
            robot_motion_hist_df = bigdataquery_dao.get_eqp_robot_motion_history(target_line, eqp_id, lot_id, step_seq, start_date, end_date,lot_id)
            
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
            return None

        ## 내 랏 READID 기준으로 나중에 오는 상태 값, 이전에 오는 상태 값 목록
        next_state = ['LPFORWARD', 'FOUPDOOROPEN', 'MAPPING', 'FOUPDOORCLOSE', 'LPDECHUCK']
        prev_state = ['PURGE_FRONT', 'PURGE_REAR', 'LPCHUCK']

        # 8. hw_motion_hist_df redis / 캐시에 조회
        hw_cache_key = f"HW_MOTION|{target_line}|{eqp_id}|{src_module_id}|{work_var}|{start_date}|{end_date}"
        hw_motion_hist_df = None

        # 8-1. Redis에서 데이터 조회
        hw_motion_hist_df, ttl = redis_cache.load_dataframe_from_redis(hw_cache_key)
        
        if hw_motion_hist_df is None or ttl is None:
            logger.info(f"No hw motion data in cache (key={hw_cache_key})")
            
            # 9. 캐시에 없으면 bigdata조회
            hw_motion_hist_df = bigdataquery_dao.get_eqp_hw_motion_history(target_line, eqp_id, src_module_id, work_var, start_date, end_date)
            
            if hw_motion_hist_df is None or hw_motion_hist_df.empty:
                logger.error('hw_motion_hist_df is empty.')
                return None
            else:
                # 10.
                redis_cache.save_dataframe_to_redis(hw_cache_key, hw_motion_hist_df)
                # starttime 기준으로 정렬, 인덱스 초기화
                hw_motion_hist_df = hw_motion_hist_df.sort_values(by=['starttime_rev'])
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
            lot_id_match_condition = hw_motion_hist_df['lot_id'].str.startswith(lot_id)
            filtered_hw_motion_hist_df = hw_motion_hist_df[((hw_motion_hist_df['wafer_id'] == wafer_id) | hw_motion_hist_df['wafer_id'] == int(wafer_id))  
                                & (hw_motion_hist_df['state'] == state_var) & lot_id_match_condition]
            
            
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
        root_lot_id, tkin, tkout, start_date, end_date, target_line = get_preprocessing_info(step_seq, eqp_id, lot_id, wafer_id)

        # target_line만 검사
        if target_line is None or (isinstance(target_line, str) and not target_line.strip()):
            logger.error(f"Preprocessing failed (target_line is None or empty): (eqp_id={eqp_id}, lot_id={lot_id}, wafer_id={wafer_id}).")
            return None
          
        # 2. Redis key 생성
        cache_key = f"PROC_MOTION|{target_line}|{eqp_id}|{lot_id}|{step_seq}|{start_date}|{end_date}"
        process_hist_df = None
        
        # 3. Redis에서 데이터 조회
        process_hist_df, ttl = redis_cache.load_dataframe_from_redis(cache_key)
        
        if process_hist_df is None :
            logger.info(f"No process_hist_df data in cache (key={cache_key})")
            
            # 4. 캐시에 없으면 bigdata조회
            process_hist_df = bigdataquery_dao.get_eqp_hw_process_history(target_line, eqp_id, start_date, end_date) 

            # mod-2.
            process_hist_df = process_hist_df[
                                ( process_hist_df['lotid'] == tkout.LOT_ID ) | ( process_hist_df['if_lot_id'] == tkout.LOT_ID )
            ]

            tkin_dt = pd.to_datetime(tkin.LOT_TRANSN_TMSTP) - pd.DateOffset(minutes=60) if tkin is not None else None
            tkout_dt = pd.to_datetime(tkout.LOT_TRANSN_TMSTP) + pd.DateOffset(minutes=60) if tkout is not None else None
            
            process_hist_df['starttime_rev'] = pd.to_datetime( process_hist_df['starttime_rev'], errors='coerce' )
            process_hist_df['endtime_rev'] = pd.to_datetime( process_hist_df['endtime_rev'], errors='coerce' )

            if tkin is not None and tkout is not None:
                process_hist_df = process_hist_df[
                                ( tkin_dt <= process_hist_df['starttime_rev'] ) & ( process_hist_df['endtime_rev'] <= tkout_dt ) ]

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

        # 운영에만 존재하는 자료를 파일로 테스트
        # process_hist_df = pd.read_csv('d:\test.txt',sep='\t')            
        # process_hist_df['wafer_id'] = process_hist_df['materialid'].apply(process_wafer_id)            
        # process_hist_df = process_hist_df.sort_values(by=['starttime_rev'])
        # process_hist_df = process_hist_df.reset_index(drop=True)

        # 09-01 수정사항
        process_hist_df = process_hist_df[
                            process_hist_df['stepname'].notnull() & (process_hist_df['stepname'].astype(str).str.strip() != "")]
        
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

        # starttime_tev, endtime_rev 컬럼의 타임존 제거
        filtered_process_hist_df['starttime_rev'] = pd.to_datetime(filtered_process_hist_df['starttime_rev'])
        filtered_process_hist_df['endtime_rev'] = pd.to_datetime(filtered_process_hist_df['endtime_rev'])
        
        # 12. 결과 있으면 time_var 설정대로 결과 생성        
        grouped = filtered_process_hist_df.groupby('moduleid')

        # 각 그룹을 starttime_rev로 오름차순 정렬
        groups = {name: group.sort_values(by='starttime_rev') for name, group in grouped}

        #각 그룹별 starttime_rev로 초소값을 기준으로 재정렬
        sorted_group_items = sorted(groups.items(), key=lamdba item: item[1]['starttime_rev'].min())

        result_list = []
        if time_var == 'START_TIME':
            # moduleid별 starttime_rev 최소값 리스트
            result_list = [group['starttime_rev'].min().tz_localize(tz=None).to_pydatetime() for name, group in sorted_group_items]
        elif time_var == 'END_TIME':
            # moduleid별 endtime_rev 최대값 리스트
            result_list = [group['endtime_rev'].max().tz_localize(tz=None).to_pydatetime() for name, group in sorted_group_items]
        elif time_var == 'PROCESS_TIME':
            # moduleid별 (endtime_rev 최대값 - starttime_rev 최소값).total_seconds() 리스트
            for name, group in sorted_group_items:
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

def mars_time_p_idle(step_seq, eqp_id, lot_id, wafer_id):
    try:    
        # 1. 전처리 작업
        root_lot_id, tkin, tkout, start_date, end_date, target_line = get_preprocessing_info(step_seq, eqp_id, lot_id, wafer_id)

        # target_line만 검사
        if target_line is None or (isinstance(target_line, str) and not target_line.strip()):
            logger.error(f"Preprocessing failed (target_line is None or empty): (eqp_id={eqp_id}, lot_id={lot_id}, wafer_id={wafer_id}).")
            return None
          
        # 2. Redis key 생성
        cache_key = f"pp_idle|{target_line}|{eqp_id}|{lot_id}|{step_seq}|{start_date}|{end_date}"
        fab_df_origin = None
        
        # 3. Redis에서 데이터 조회
        fab_df_origin, ttl = redis_cache.load_dataframe_from_redis(cache_key)
        
        if fab_df_origin is None or ttl is None:
            logger.info(f"No fab_df_origin data in cache (key={cache_key})")
            
            # 4. 캐시에 없으면 bigdata조회
            fab_df_origin = bigdataquery_dao.get_eqp_p_idle_history((target_line, eqp_id, start_date, end_date) )

            if fab_df_origin.empty:
                return None
                
            #fab_df_origin = fab_df_origin.dropna(subset=['if_lot_id','if_step_seq']).reset_index(drop=True)           
            fab_df_origin['wafer_id'] =  fab_df_origin['materialid'].apply(process_wafer_id)
            fab_df_origin = fab_df_origin.sort_values(by='starttime_rev').reset_index(drop=True)
            
            if fab_df_origin is None or fab_df_origin.empty:
                logger.error('p_idle data is empty.')
                return None                
            else:
                redis_cache.save_dataframe_to_redis(cache_key, fab_df_origin)
        else:
            logger.info(f"found p_idle data in cache (key={cache_key})")
                                                 
        fab_df = fab_df_origin.copy()

        # mod-3. tkin, tkout의 LOT_TRANSN_TMSTP에서 타임존 제거
        tkin_dt = pd.to_datetime(tkin.LOT_TRANSN_TMSTP) - pd.DateOffset(minutes=60) if tkin is not None else None
        tkout_dt = pd.to_datetime(tkout.LOT_TRANSN_TMSTP) - pd.DateOffset(minutes=60) if tkout is not None else None    

        if hasattr(tkin_dt, "tz_localize"):
            tkin_dt = tkin_dt.tz_localize(None)
        if hasattr(tkout_dt, "tz_localize"):
            tkout_dt = tkout_dt.tz_localize(None)              
            
        # 5. material_id를 알아내야 한다    
        filtered_df_temp = fab_df[
                        (fab_df['lotid'] == tkout.LOT_ID) |  (fab_df['if_lot_id'] == tkout.LOT_ID)
                        & ((fab_df['wafer_id'] == wafer_id) | (fab_df['wafer_id'] == int(wafer_id))) 
                        ].reset_index(drop=True)    

        # starttime_tev, endtime_rev 컬럼의 타임존 제거
        filtered_df_temp['starttime_rev'] = pd.to_datetime(filtered_df_temp['starttime_rev']).dt.tz_localize(None)
        filtered_df_temp['endtime_rev'] = pd.to_datetime(filtered_df_temp['endtime_rev']).dt.tz_localize(None)
        
        if tkin is not None and tkout is not None :
            filtered_df_temp = filtered_df_temp[
                (tkin_dt <= filtered_df_temp['starttime_rev']) & (filtered_df_temp['endtime_rev'] <= tkout_dt)
            ]
            
        if not filtered_df_temp.empty:       
            # wafer_id로 정확히 걸러야 한다.
            filtered_df_temp = filtered_df_temp[(filtered_df_temp['wafer_id'] == wafer_id) | (filtered_df_temp['wafer_id'] == int(wafer_id))]
            material_id = filtered_df_temp['materialid'].iloc[0]
        else:
            return [[-1], [-1]]  # 두 결과 모두 -1로 반환

        # mod 조건 추가 대괄호추가 0924
        filtered_df = fab_df[
                            (fab_df['materialid'] == material_id) & 
                            ((fab_df['lotid'] == tkout.LOT_ID ) | (fab_df['if_lot_id'] == tkout.LOT_ID))
                      ].reset_index(drop=True)

        # starttime_rev, endtime_rev 컬럼의 타임존 제거
        filtered_df['starttime_rev'] = pd.to_datetime(filtered_df['starttime_rev']).dt.tz_localize(None)
        filtered_df['endtime_rev'] = pd.to_datetime(filtered_df['endtime_rev']).dt.tz_localize(None)

        if tkin is not None and tkout is not None :
            filtered_df = filtered_df[(tkin_dt <= filtered_df['starttime_rev']) & 
                                        (filtered_df['endtime_rev'] <= tkout_dt)]
              
        moduleid_distinct = filtered_df['moduleid'].drop_duplicates().tolist()
        
        def calc_p_idle_result(fab_df_input, material_id, moduleid_distinct):
            result = []
            for module_id in moduleid_distinct:
                fab_df_temp = fab_df_input[fab_df_input['moduleid'] == module_id].sort_values(by=['starttime_rev', 'endtime_rev'], ascending=True).reset_index(drop=True)

                fab_df_temp['starttime_rev'] = pd.to_datetime(fab_df_temp['starttime_rev']).dt.tz_localize(None)
                fab_df_temp['endtime_rev'] = pd.to_datetime(fab_df_temp['endtime_rev']).dt.tz_localize(None)

                tkin_dt = pd.to_datetime(tkin.LOT_TRANSN_TMSTP) - pd.DateOffset(minutes=60) if tkin is not None else None
                tkout_dt = pd.to_datetime(tkout.LOT_TRANSN_TMSTP) - pd.DateOffset(minutes=60) if tkout is not None else None    

                fab_df_temp_pos = fab_df_temp[(tkin_dt <= fab_df_temp['starttime_rev']) & (fab_df_temp['endtime_rev'] <= tkout_dt)]
                
                # 기본 조건과 prefix 변경 조건을 결합
                basic_condition = fab_df_temp_pos['materialid'] == material_id
                # prefix_change_condition = (fab_df_temp_pos['materialid_prefix'] != fab_df_temp_pos['prev_materialid_prefix']) | fab_df_temp_pos['prev_materialid_prefix'].isna()

                lot_id_condition = ((fab_df_temp_pos['lotid'] == tkout.LOT_ID ) | (fab_df_temp_pos['if_lot_id'] == tkout.LOT_ID))              
                match = fab_df_temp_pos[basic_condition & lot_id_condition].index
                
                if not match.empty:
                    cur_idx = match[0]
                    cur_start_time = fab_df_temp.loc[cur_idx, 'starttime_rev'].tz_localize(tz=None)
                    pre_end_time = None

                    try:
                        for offset in range(1, 9):
                            prev_idx = cur_idx - offset
                            if prev_idx < 0:
                                result.append(-1)
                                break
                            prev_start_time = fab_df_temp.loc[prev_idx, 'starttime_rev'].tz_localize(tz=None)
                            time_diff_sec = abs((cur_start_time - prev_start_time).total_seconds())
                            if time_diff_sec > 1:
                                pre_end_time = fab_df_temp.loc[prev_idx, 'endtime_rev'].tz_localize(tz=None)
                                break
                        if pre_end_time is not None:
                            time_diff = (cur_start_time - pre_end_time).total_seconds()
                            result.append(time_diff)        
                    except Exception as e:
                        logger.error(f"이전 wafer 찾을때 오류 발생함: {e}")
                        result.append(-1)
            return result

        # 1. 전체 데이터로 계산
        result = calc_p_idle_result(fab_df, material_id, moduleid_distinct)        
        # 2. materialid가 'EMPTY'가 아닌 데이터로 계산
        fab_df_filter = fab_df_origin[(fab_df_origin['materialid'].str.strip() != 'EMPTY') & (fab_df_origin['stepname'] != "")].copy()
        # 2-1. stepname is notna 인 데이터로 계산
        fab_df_filter = fab_df_filter.dropna(subset=['stepname']).reset_index(drop=True)
        
        filtered_df_filter = fab_df_filter[
            (fab_df_filter['materialid'] == material_id) & 
            ((fab_df_filter['lotid'] == tkout.LOT_ID ) | (fab_df_filter['if_lot_id'] == tkout.LOT_ID))
        ].reset_index(drop=True)

        filtered_df_filter['starttime_rev'] = pd.to_datetime(filtered_df_filter['starttime_rev']).dt.tz_localize(None)
        filtered_df_filter['endtime_rev'] = pd.to_datetime(filtered_df_filter['endtime_rev']).dt.tz_localize(None)

        if tkin is not None and tkout is not None:
            filtered_df_filter = filtered_df_filter[
                (tkin_dt <= filtered_df_filter['starttime_rev']) & 
                (filtered_df_filter['endtime_rev'] <= tkout_dt)
            ]

        moduleid_distinct_filter = filtered_df_filter['moduleid'].drop_duplicates().tolist()

        # 전체데이타에서 'materialid'가 'EMPTY'가 아니고  'stepname' != '' 인 자료에서 검색
        result_filter = calc_p_idle_result(fab_df_filter, material_id, moduleid_distinct_filter)

        # 3. 두 결과를 [ [a,b] for a,b in zip(result, result_filter) ] 형태로 반환
        result_new = [ [a, b] for a, b in zip(result, result_filter) ]
        return result_new
        
    except Exception as e:
        logger.exception(f"Error in mars_time_p_idle: {str(e)}")
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

    



