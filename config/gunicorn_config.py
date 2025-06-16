workers = 5
# 단일 쓰레드로 설정
threads = 5
daemon = True
preload_app = True
# 타임아웃은 15분 (bigdataquery 자체 타임아웃 10 분 + 마진 5분)
timeout = 15 * 60
# max requests = n 개 요청 수행후 워커 자동 재시작
max_requests = 1000
# 모든 워커가 동시 재시작 되는것을 방지하기 위해 워커별로 1 ~ n 개 요청 랜덤하게 추가 수행후 재시작
max_requests_jitter = 1000
bind = 'localhost:6011'
logconfig = 'config/gunicorn_logging.conf'
proc_name = 'space_ui_if_service'