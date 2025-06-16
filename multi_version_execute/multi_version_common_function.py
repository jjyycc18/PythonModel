import numpy as np

def check_dimensions(target_list):
  dims = []
  while isinstance(target_list, list) and target_list is not None:
    dims.append(len(target_list))
    target_list - target_list[0]
  return len(dis)

def convert_serializable_result(result):
  if isinstance(result, np.ndarray):
    return result.tolist()
  elif  isinstance(result,,list):
    return ap.array(result, dtype=float).tolist()
  else:
    return float(result)
