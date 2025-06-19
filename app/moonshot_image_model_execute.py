from multi_version_execute import multi_version_gpu_executor_client

def execute_moonshot_image_model(tmp_seq,model_path,lot_id,wafer_id,step_seq,eqp_id,run_mode=None):
  wisc_image_info, wisc_ftp_info = get_wisc_image_info(lot_id, wafer_id, step_seq, eqp_id)
  if wisc_image_info is None or wisc_ftp_info is None:
    return None, None
  image_url = convert_image_url_sepatator(wisc_image_info['ImageUrl']
  image_download_path = generate_moonshot_image_download_path(lot_id, step_seq, eqp_id, image_url)
  if not download_wisc_image(image_url, image_download_path, wisc_ftp_info):
    return None, None
  result_path = generate_moonshot_image_result_path(tmp_seq, lot_id, wafer_id)
  param_dict = {
    "task_type": constants.MOONSHOT_IMAGE,
    "param_dict": {
      "MODEL_PATH": model_path
      "IMAGE_PATH": image_path
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

  return avg_rsult, site_result

def convert_image_url_separator(image_url):
  pass

def generate_moonshot_image_download_path(lot_id, step_seq, eqp_id, image_url):
  pass
  
def generate_moonshot_image_resule_path(tmp_seq, lot_id, wafer_id):
  pass
  
def generate_resule_value(result_dict):
  pass
  
def generate_resule_info(result_dict, wisc_image_info):
  pass
  
def generate_top_resule_info(result_dict, wisc_image_info):
  pass
  
def upload_result_images(ftp_upload_path, result_path, wisc_ftp_info):
  pass
    
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
  pass

def get_moonshot_image_path_for_delete_fob():
  pass

if __name == "__main__":

  tmp_seq = 1234
  eqp_id = 'test001'
  step_seq = 'step001'
  lot_id = 'lot01'
  wafer_id = '08'
  model_path = 'd:/appli/mooshot/wisc_aomaly_dec_001'

execute_moonshot_image_model(tmtmp_seq,model_path,lot_id,wafer_id,step_seq,eqp_id, run_mode=constants.RUN_MODE_SERVER)








































