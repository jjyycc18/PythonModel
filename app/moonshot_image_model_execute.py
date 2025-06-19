import os
import logging
import ftplib
import shutil
import datetime
from pathlib import Path
from net.space_request_client import HttpRequestClient
from dao import vm_dao
from common import constants
from config import config
from multi_version_execute import multi_version_gpu_executor_client

logger = logging.getLogger(__name__)

def execute_moonshot_image_model(tmp_seq,model_path,lot_id,wafer_id,step_seq,eqp_id,run_mode=None):
  wisc_image_info, wisc_ftp_info = get_wisc_image_info(lot_id, wafer_id, step_seq, eqp_id)
  if wisc_image_info is None or wisc_ftp_info is None:
    return None, None
  image_url = convert_image_url_separator(wisc_image_info['ImageUrl'])
  image_download_path = generate_moonshot_image_download_path(lot_id, step_seq, eqp_id, image_url)
  if not download_wisc_image(image_url, image_download_path, wisc_ftp_info):
    return None, None
  result_path = generate_moonshot_image_result_path(tmp_seq, lot_id, wafer_id)
  param_dict = {
    "task_type": constants.MOONSHOT_IMAGE,
    "param_dict": {
      "MODEL_PATH": model_path,
      "IMAGE_PATH": image_download_path,
      "RESULT_PATH": result_path
    }
  }
  env = vm_dao.get_vm_space_model_tmp_info(tmp_seq).ENVIROMENT
  moonshot_result_dict = multi_version_gpu_executor_client.gpu_model_execution_task_proc(tmp_seq, param_dict, env)
  if moonshot_result_dict is None:
    return None, None

  #모델 결과값 생성
  avg_result, site_result = generate_result_value(moonshot_result_dict)
  if run_mode == constants.RUN_MODE_INFERENCE:
    return avg_result, site_result

  if not len(os.listdir(result_path)) > 0:
    return avg_result, site_result

  ftp_upload_path = os.path.dirname(image_url)
  #fpt메 결과 이미지 파일 업로드
  if not upload_result_images(ftp_upload_path, result_path, wisc_ftp_info):
    return avg_result, site_result


  #fpt 업로드 잘 되면 결과 업데이트 요청 메세지 전송
  result_info = generate_result_info(moonshot_result_dict, wisc_image_info)
  result_info_reply = send_result_info(result_info)

  return avg_result, site_result

def convert_image_url_separator(image_url):
  """이미지 URL의 구분자를 변환합니다."""
  if image_url is None:
    return None
  
  # Windows 경로 구분자를 Unix 경로 구분자로 변환
  converted_url = image_url.replace('\\', '/')
  return converted_url

def generate_moonshot_image_download_path(lot_id, step_seq, eqp_id, image_url):
  """Moonshot 이미지 다운로드 경로를 생성합니다."""
  if not image_url:
    return None
  
  # 기본 다운로드 디렉토리
  base_download_dir = config.moonshot_image.get('download_path', '/tmp/moonshot_download')
  
  # 파일명 추출
  filename = os.path.basename(image_url)
  
  # 경로 생성: base_dir/lot_id/step_seq/eqp_id/filename
  download_path = os.path.join(base_download_dir, lot_id, step_seq, eqp_id, filename)
  
  # 디렉토리 생성
  os.makedirs(os.path.dirname(download_path), exist_ok=True)
  
  return download_path
  
def generate_moonshot_image_result_path(tmp_seq, lot_id, wafer_id):
  """Moonshot 이미지 결과 경로를 생성합니다."""
  # 기본 결과 디렉토리
  base_result_dir = config.moonshot_image.get('result_path', '/tmp/moonshot_result')
  
  # 경로 생성: base_dir/tmp_seq/lot_id/wafer_id
  result_path = os.path.join(base_result_dir, str(tmp_seq), lot_id, wafer_id)
  
  # 디렉토리 생성
  os.makedirs(result_path, exist_ok=True)
  
  return result_path
  
def generate_result_value(result_dict):
  """결과 딕셔너리에서 평균값과 사이트별 결과를 추출합니다."""
  if not result_dict:
    return None, None
  
  try:
    # 평균 결과값 추출 (예시)
    avg_result = result_dict.get('avg_result', 0.0)
    
    # 사이트별 결과 추출 (예시)
    site_result = result_dict.get('site_result', {})
    
    return avg_result, site_result
  except Exception as e:
    logger.error(f"결과값 생성 중 오류 발생: {e}")
    return None, None
  
def generate_result_info(result_dict, wisc_image_info):
  """결과 정보를 생성합니다."""
  if not result_dict or not wisc_image_info:
    return None
  
  try:
    result_info = {
      'image_info': wisc_image_info,
      'result_data': result_dict,
      'timestamp': datetime.datetime.now().isoformat()
    }
    return result_info
  except Exception as e:
    logger.error(f"결과 정보 생성 중 오류 발생: {e}")
    return None
  
def generate_top_result_info(result_dict, wisc_image_info):
  """TOP 결과 정보를 생성합니다."""
  if not result_dict or not wisc_image_info:
    return None
  
  try:
    top_result_info = {
      'image_info': wisc_image_info,
      'top_result_data': result_dict,
      'timestamp': datetime.datetime.now().isoformat()
    }
    return top_result_info
  except Exception as e:
    logger.error(f"TOP 결과 정보 생성 중 오류 발생: {e}")
    return None
  
def upload_result_images(ftp_upload_path, result_path, wisc_ftp_info):
  """결과 이미지들을 FTP 서버에 업로드합니다."""
  if not ftp_upload_path or not result_path or not wisc_ftp_info:
    return False
  
  try:
    # FTP 연결 정보
    ftp_host = wisc_ftp_info.get('host')
    ftp_user = wisc_ftp_info.get('username')
    ftp_pass = wisc_ftp_info.get('password')
    ftp_port = wisc_ftp_info.get('port', 21)
    
    if not all([ftp_host, ftp_user, ftp_pass]):
      logger.error("FTP 연결 정보가 불완전합니다.")
      return False
    
    # FTP 연결
    ftp = ftplib.FTP()
    ftp.connect(ftp_host, ftp_port)
    ftp.login(ftp_user, ftp_pass)
    
    # 결과 디렉토리의 모든 파일 업로드
    for filename in os.listdir(result_path):
      file_path = os.path.join(result_path, filename)
      if os.path.isfile(file_path):
        with open(file_path, 'rb') as file:
          ftp.storbinary(f'STOR {filename}', file)
    
    ftp.quit()
    logger.info(f"결과 이미지 업로드 완료: {result_path} -> {ftp_upload_path}")
    return True
    
  except Exception as e:
    logger.error(f"FTP 업로드 중 오류 발생: {e}")
    return False
    
def send_result_info(result_info):
  result = HttpRequestClient(config.moonshot_image['result_api_url'], result_info).get_result()
  return result
  
def send_top_result_info(result_info):
  result = HttpRequestClient(config.moonshot_image['top_result_api_url'], result_info).get_result()
  return result
  
def get_wisc_image_info(lot_id,wafer_id,step_seq,eqp_id):  
  param_dict = {"EqpId": eqp_id, "StepSeq": step_seq, "LotId": lot_id, "WaferId": int(wafer_id)}
  
  result = HttpRequestClient(config.moonshot_image['image_api_url'], param_dict).get_result()
  
  if result is None or len(result) == 0:
    return None, None
  else:
    return result['Image'][0], result['Connection']  

def download_wisc_image(image_url, image_download_path, wisc_ftp_info):
  """WISC 이미지를 FTP에서 다운로드합니다."""
  if not image_url or not image_download_path or not wisc_ftp_info:
    return False
  
  try:
    # FTP 연결 정보
    ftp_host = wisc_ftp_info.get('host')
    ftp_user = wisc_ftp_info.get('username')
    ftp_pass = wisc_ftp_info.get('password')
    ftp_port = wisc_ftp_info.get('port', 21)
    
    if not all([ftp_host, ftp_user, ftp_pass]):
      logger.error("FTP 연결 정보가 불완전합니다.")
      return False
    
    # FTP 연결
    ftp = ftplib.FTP()
    ftp.connect(ftp_host, ftp_port)
    ftp.login(ftp_user, ftp_pass)
    
    # 파일명 추출
    filename = os.path.basename(image_url)
    
    # 디렉토리 생성
    os.makedirs(os.path.dirname(image_download_path), exist_ok=True)
    
    # 파일 다운로드
    with open(image_download_path, 'wb') as file:
      ftp.retrbinary(f'RETR {filename}', file.write)
    
    ftp.quit()
    logger.info(f"이미지 다운로드 완료: {image_url} -> {image_download_path}")
    return True
    
  except Exception as e:
    logger.error(f"이미지 다운로드 중 오류 발생: {e}")
    return False

def get_moonshot_image_path_for_delete_fob():
  """삭제할 Moonshot 이미지 경로를 가져옵니다."""
  try:
    # 설정에서 삭제 대상 경로 가져오기
    delete_path = config.moonshot_image.get('delete_path', '/tmp/moonshot_old')
    
    if os.path.exists(delete_path):
      return delete_path
    else:
      return None
  except Exception as e:
    logger.error(f"삭제 경로 조회 중 오류 발생: {e}")
    return None

if __name__ == "__main__":
  tmp_seq = 1234
  eqp_id = 'test001'
  step_seq = 'step001'
  lot_id = 'lot01'
  wafer_id = '08'
  model_path = 'd:/appli/mooshot/wisc_aomaly_dec_001'

  execute_moonshot_image_model(tmp_seq,model_path,lot_id,wafer_id,step_seq,eqp_id, run_mode=constants.RUN_MODE_SERVER)








































