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

