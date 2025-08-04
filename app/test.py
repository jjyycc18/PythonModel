'''
bigdataquery api 로그에 get_eqp_hw_process_history() 테이블조회시 아래와 같이 동일 조건으로 반복조회 하는 경우가 많이보인다.
get_eqp_robot_motion_history(),get_eqp_hw_motion_history() 은 반복조회되지 않는다, 혹시 조회 로직에 개선할 부분이 있나?

'로그예시'
2025-08-04 11:10:49  [223331] [13999999992316] INFO BigdataqueryGetData called.
2025-08-04 11:10:49  [223331] [13999999992316] INFO BigdataqueryGetData : client_ip=127.0.0.1, query_param={'table_name': 'fab.m_fab_process','equipmentid': 'cp0001','if_step_seq':'cr001','if_lot_id': 'padf111','dateFrom': '2025-08-03','dateTo': '2025-08-04','like_conditions' : {'targetline' : '%A1%'}},custom_columns=['area', 'equipmentid', 'moduleid', 'workgroup', 'state', 'starttime', 'endtime', 'starttime_rev', 'endtime_rev', 'materialid', 'recipename', 'stepno', 'stepname', 'if_step_seq', 'if_lot_id', 'if_tkin_date']
2025-08-04 11:10:50  [223331] [13999999992316] INFO BigdataqueryGetData completed.
2025-08-04 11:10:53  [223331] [13999999992316] INFO BigdataqueryGetData called.
2025-08-04 11:10:49  [223331] [13999999992316] INFO BigdataqueryGetData : client_ip=127.0.0.1, query_param={'table_name': 'fab.m_fab_process','equipmentid': 'cp0001','if_step_seq':'cr001','if_lot_id': 'padf111','dateFrom': '2025-08-03','dateTo': '2025-08-04','like_conditions' : {'targetline' : '%A1%'}},custom_columns=['area', 'equipmentid', 'moduleid', 'workgroup', 'state', 'starttime', 'endtime', 'starttime_rev', 'endtime_rev', 'materialid', 'recipename', 'stepno', 'stepname', 'if_step_seq', 'if_lot_id', 'if_tkin_date']
2025-08-04 11:10:54  [223331] [13999999992316] INFO BigdataqueryGetData completed.
2025-08-04 11:10:54  [223331] [13999999992316] INFO BigdataqueryGetData called.
2025-08-04 11:10:49  [223331] [13999999992316] INFO BigdataqueryGetData : client_ip=127.0.0.1, query_param={'table_name': 'fab.m_fab_process','equipmentid': 'cp0001','if_step_seq':'cr001','if_lot_id': 'padf111','dateFrom': '2025-08-03','dateTo': '2025-08-04','like_conditions' : {'targetline' : '%A1%'}},custom_columns=['area', 'equipmentid', 'moduleid', 'workgroup', 'state', 'starttime', 'endtime', 'starttime_rev', 'endtime_rev', 'materialid', 'recipename', 'stepno', 'stepname', 'if_step_seq', 'if_lot_id', 'if_tkin_date']
2025-08-04 11:10:58  [223331] [13999999992316] INFO BigdataqueryGetData completed.
'''
