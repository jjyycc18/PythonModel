def gpu_model_execution_task_proc(tmp_seq:int, param_dict:dict, env:str):
  max_free_gpu = select_task_execution_server(env)
  if max_free_gpu is None:
    return None
  base_url = max_free_fpu['base_url']
  task_id = add_gpu_model_execution_task(base_url,param_dict)
  if task_id is None:
    return None
  try:
    status = wait_add_gpu_model_execution_task(task_id, base_id)
    task_result = get_gpu_model_execution_task_result(task_id, base_id)
    if status == constants.GPU_MODEL_EXECUTOR_SUCCESS:
      return task_result
  except TimeoutError as e:
    logger.exception('')
  except Exception as e:
    logger.exception('')

  return None

if __name__ == '__main__'
  tmp_seq = 1317
  param_dict = {
    "task_type": "13"
    ,"param_dict":{
      "MODEL_PATH": "D:/TEST/TMAGEAI/"
      "IMAGE_PATH": "D:/TEST/TMAGEAI/IMAGE/TEST"
      "RESULT_PATH": "D:/TEST/TMAGEAI/RESULT"
    }
  }
task_result = gpu_model_execution_task_proc(tmp_seq, param_dict, 'PY37')
print(task_result)
    
