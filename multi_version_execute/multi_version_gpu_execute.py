import sys
import logging
import torch
import gc
import importlib
from numpyencoder import NumpyEncoder
import pickle
import json
import numpy as np
import os
from pynvml import nvmlInit, nvmlDeviceGetCount, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo, nvmlShutdown, nvmlDeviceGetMaxMigDeviceCount, nvmlDeviceGetMigDeviceHandleByIndex, nvmlDeviceGetUUID

logger = logging.getLogger(__name__)

def execute_moonshot_image_model(model_path, image_path, result_path):
    logger.info('## start')
    result = execute_torch_script(model_path, image_path, result_path, main_func='run', main_fname='main.py', model_path=model_path)
    logger.info('## completed')
    return result

def execute_torch_script(*args, **kwargs):
    model_path = None
    try:
        main_func = kwargs['main_func']
        main_fname = kwargs['main_fname']
        model_path = kwargs['model_path']
        del kwargs['main_func']
        del kwargs['main_fname']
        del kwargs['model_path']

        sys.path.append(model_path)

        # torch gpu 할당
        allocate_gpu()
        with open(os.path.join(model_path, main_fname), encoding='UTF-8') as f:
            model_script = f.read()
            local_dict = {}
            exec(model_script, local_dict)
        with torch.cuda.stream(torch.cuda.Stream()):
            result = local_dict[main_func](*args, **kwargs)

    except Exception as e:
        logger.info('## exception occurred')
        raise
        
    finally:
        if model_path is not None:
            sys.path.remove(model_path)
        torch.cuda.empty_cache()
        gc.collect()
        
    return result

def allocate_gpu():
    device_uuid, freem = get_free_gpu_mem()
    os.environ["CUDA_VISIBLE_DEVICES"] = device_uuid
    torch.set_num_threads(1)

def get_free_gpu_mem():
    try:
        nvmlInit()
        device_count = nvmlDeviceGetCount()
        freem = []
        uuids = []  # 현재 서버에 설정된 gpu 인스턴스
        for i in range(device_count):
            nvml_handle = nvmlDeviceGetMigDeviceHandleByIndex(i)
            mig_max_device_cnt = nvmlDeviceGetMaxMigDeviceCount(nvml_handle)
            if mig_max_device_cnt == 0:
                freem.append(nvmlDeviceGetMemoryInfo(nvml_handle).free)
                uuids.append(nvmlDeviceGetUUID(nvml_handle))
            else:
                for k in range(mig_max_device_cnt):
                    try:
                        nvml_mig_handle = nvmlDeviceGetMigDeviceHandleByIndex(nvml_handle, k)
                        freem.append(nvmlDeviceGetMemoryInfo(nvml_mig_handle).free)
                        uuids.append(nvmlDeviceGetUUID(nvml_mig_handle))
                    except Exception as e:
                        break
        # 여유 공간이 가장 높은 gpu instance idx
        device_idx = np.argmax(freem).item()
        return uuids[device_idx], round(freem[device_idx] / 1024 ** 3, 2)
        
    finally:
        nvmlShutdown()

if __name__ == "__main__":
    model_path = 'D:/moonshot/model'
    image_path = 'D:/test_data/moonshot/model.jpg'
    result_path = 'D:/test_data/moonshot/result'
    execute_moonshot_image_model(model_path, image_path, result_path)
          
    
