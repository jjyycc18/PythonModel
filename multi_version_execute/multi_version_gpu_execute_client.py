import logging
import time
import requests
from net.space_request_client import HttpRequestClient
from config import config
from common import constants

logger = logging.getLogger(__name__)

def select_task_execution_server(env):
  """환경에 맞는 GPU 실행 서버를 선택합니다."""
  try:
    # 환경별 GPU 서버 URL 가져오기
    gpu_servers = config.get('gpu_executor', {})
    if env not in gpu_servers:
      logger.error(f"환경 {env}에 대한 GPU 서버 설정이 없습니다.")
      return None
    
    base_url = gpu_servers[env]
    
    # 서버 상태 확인
    try:
      health_check_url = f"{base_url}/health"
      response = requests.get(health_check_url, timeout=5)
      if response.status_code == 200:
        return {'base_url': base_url, 'status': 'available'}
    except Exception as e:
      logger.warning(f"GPU 서버 {base_url} 상태 확인 실패: {e}")
    
    return {'base_url': base_url, 'status': 'unknown'}
    
  except Exception as e:
    logger.error(f"GPU 실행 서버 선택 중 오류 발생: {e}")
    return None

def add_gpu_model_execution_task(base_url, param_dict):
  """GPU 모델 실행 태스크를 추가합니다."""
  try:
    task_url = f"{base_url}/addTask"
    rc = HttpRequestClient(task_url, param_dict, timeout=60)
    result = rc.get_result()
    
    if result and 'task_id' in result:
      logger.info(f"GPU 태스크 추가 완료: {result['task_id']}")
      return result['task_id']
    else:
      logger.error("GPU 태스크 추가 실패: 응답에 task_id가 없습니다.")
      return None
      
  except Exception as e:
    logger.error(f"GPU 태스크 추가 중 오류 발생: {e}")
    return None

def wait_add_gpu_model_execution_task(task_id, base_url, timeout=300):
  """GPU 모델 실행 태스크 완료를 기다립니다."""
  try:
    start_time = time.time()
    while time.time() - start_time < timeout:
      status_url = f"{base_url}/taskStatus/{task_id}"
      rc = HttpRequestClient(status_url, {}, timeout=10)
      result = rc.get_result()
      
      if result and 'status' in result:
        status = result['status']
        if status == 'completed':
          logger.info(f"GPU 태스크 완료: {task_id}")
          return constants.GPU_MODEL_EXECUTOR_SUCCESS
        elif status == 'failed':
          logger.error(f"GPU 태스크 실패: {task_id}")
          return 'FAILED'
        elif status == 'processing':
          logger.debug(f"GPU 태스크 처리 중: {task_id}")
          time.sleep(5)  # 5초 대기
        else:
          logger.warning(f"알 수 없는 GPU 태스크 상태: {status}")
          time.sleep(5)
      else:
        logger.warning(f"GPU 태스크 상태 조회 실패: {task_id}")
        time.sleep(5)
    
    logger.error(f"GPU 태스크 타임아웃: {task_id}")
    raise TimeoutError(f"GPU 태스크 {task_id} 실행 타임아웃")
    
  except TimeoutError:
    raise
  except Exception as e:
    logger.error(f"GPU 태스크 대기 중 오류 발생: {e}")
    return 'ERROR'

def get_gpu_model_execution_task_result(task_id, base_url):
  """GPU 모델 실행 태스크 결과를 가져옵니다."""
  try:
    result_url = f"{base_url}/taskResult/{task_id}"
    rc = HttpRequestClient(result_url, {}, timeout=30)
    result = rc.get_result()
    
    if result and 'result' in result:
      logger.info(f"GPU 태스크 결과 조회 완료: {task_id}")
      return result['result']
    else:
      logger.error(f"GPU 태스크 결과 조회 실패: {task_id}")
      return None
      
  except Exception as e:
    logger.error(f"GPU 태스크 결과 조회 중 오류 발생: {e}")
    return None

def gpu_model_execution_task_proc(tmp_seq:int, param_dict:dict, env:str):
  max_free_gpu = select_task_execution_server(env)
  if max_free_gpu is None:
    return None
  base_url = max_free_gpu['base_url']
  task_id = add_gpu_model_execution_task(base_url,param_dict)
  if task_id is None:
    return None
  try:
    status = wait_add_gpu_model_execution_task(task_id, base_url)
    task_result = get_gpu_model_execution_task_result(task_id, base_url)
    if status == constants.GPU_MODEL_EXECUTOR_SUCCESS:
      return task_result
  except TimeoutError as e:
    logger.exception('')
  except Exception as e:
    logger.exception('')

  return None

if __name__ == '__main__':
  tmp_seq = 1317
  param_dict = {
    "task_type": "13",
    "param_dict": {
      "MODEL_PATH": "D:/TEST/TMAGEAI/",
      "IMAGE_PATH": "D:/TEST/TMAGEAI/IMAGE/TEST",
      "RESULT_PATH": "D:/TEST/TMAGEAI/RESULT"
    }
  }
  task_result = gpu_model_execution_task_proc(tmp_seq, param_dict, 'PY37')
  print(task_result)
    
