mars_time_p_idle() 의 로직에 추가개발이 필요하다. (반드시 기존에 수행되는 결과는 바뀌면 안된다.)
starttime_rev가 같은 wafer가 최대 4장이 될 수 있는 경우가 발생하게 되어서 수정이 필요하다

##해결방안
1. 동시 투입되는 wafer의 현재 시간별로 그룹핑되도록 endtime_rev에 sort 기준을 추가한다. (현재 wafer의 바로 위 row가 이전 wafer또는 동시 투입된 wafer와 동일한 시간이 되도록 정렬) 
2. 현재 wafer의 위의 row들을 하나씩 체크하면서 이전 투입된 wafer인지 판단 (row의 역순으로 현재 wafer의 starttime_rev와 비교해서 이전 wafer를 찾아 p_idle계산)
3. p_idle 이전 wafer를 찾기위한 예시코드
  -sample code
   '''
    fab_df_temp = fab_df_temp[fab_df['moduleid'] == x].sort_values(by=['starttime_rev','endtime_rev'], ascending=True).reset_index(drop=True)
   '''
5. 이전 row 의 starttime_rev가 동일한지 확인해거 체크하는 예시 코드
   -sample code
   '''
    try:
     if (fab_df_temp['starttime_rev'][cur_idx] != fab_df_temp['starttime_rev'][cur_ids-1]):
       pre_end_time = pd.to_datetime(df['endtime_rev'][cur_ids-1], errors='coerce')
     elif (fab_df_temp['starttime_rev'][cur_idx] != fab_df_temp['starttime_rev'][cur_ids-2]):
       pre_end_time = pd.to_datetime(df['endtime_rev'][cur_ids-2], errors='coerce')
     elif (fab_df_temp['starttime_rev'][cur_idx] != fab_df_temp['starttime_rev'][cur_ids-3]):
       pre_end_time = pd.to_datetime(df['endtime_rev'][cur_ids-3], errors='coerce')
     elif (fab_df_temp['starttime_rev'][cur_idx] != fab_df_temp['starttime_rev'][cur_ids-4]):
       pre_end_time = pd.to_datetime(df['endtime_rev'][cur_ids-4], errors='coerce')
    except Exception as e:
       print(f"이전 wafer 찾을때 오류 발생함: {e}") 
   '''
