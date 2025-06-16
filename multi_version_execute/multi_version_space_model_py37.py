import json
import numpy as np
import lightgbm as lgb
import xgboost as xgb
import sys
import tensorflow as tf
from common import constants
import logging
import torch
import sklearn_json as skljson
from .space_rf import SpaceRFRegressor, SpaceRFClassifier

logger = logging.getLogger(__name__)

class KerasModel:
    def __init__(self, path):
        tf.config.set_visible_devices([], 'GPU')
        self.code = constants.KERAS
        self.model = tf.keras.models.load_model(path, compile=False)

    def predict(self, X):
        return self.model.predict_on_batch(X)
    
class LightGBMModel:
    def __init__(self, path, problem_type=constants.REGRESSION):
        self.code = constants.LIGHTGBM
        self.problem_type = problem_type
        self.model = lgb.Booster(model_file=path)

    def predict(self, X):
        y_pred = self.model.predict(X)
        if constants.CLASSIFICATION == self.problem_type:
            y_pred = np.log(y_pred)
            y_pred = np.clip(y_pred, np.log(sys.float_info.min), float('inf'))
        return y_pred

class XGBoostModel:
    def __init__(self, path, problem_type=constants.REGRESSION):
        self.code = constants.XGBOOST
        self.model = xgb.Booster()
        self.problem_type = problem_type
        self.model.load_model(path)

    def predict(self, X):
        X = xgb.DMatrix(data=X)
        y_pred = self.model.predict(X)
        if constants.CLASSIFICATION == self.problem_type:
            y_pred = np.log(y_pred)
            y_pred = np.clip(y_pred, np.log(sys.float_info.min), float('inf'))
        return y_pred

class RidgeModel:
    def __init__(self, path, problem_type=constants.REGRESSION):
        self.code = constants.RIDGE
        self.model = skljson.from_json(path)
        self.problem_type = problem_type

    def predict(self, X):
        y_pred = self.model.predict(X)
        if len(y_pred.shape) == 1:
            y_pred = y_pred.reshape(-1, 1)
        return y_pred

class RandomForestModel:
    def __init__(self, path, problem_type=constants.REGRESSION):
        self.code = constants.RANDOM_FOREST
        if problem_type == constants.REGRESSION:
            self.model = SpaceRFRegressor()
        else:  
            self.model = SpaceRFClassifier()
        self.model.load_model(path)  

    def predict(self, X):
        y_pred = self.model.predict(X)
        if len(y_pred.shape) == 1:
            y_pred = y_pred.reshape(-1, 1)
        return y_pred
    
class TorchModel:
    def __init__(self, path):
        self.code = constants.TORCH
        self.model = torch.jit.load(path)

    def predict(self, X):
        y_pred = self.model.forward(X).cpu().detach().numpy()
        return y_pred

def execute_model(model, normVmData):
    logger.debug("model execute called !!")
    
    if multi_version_common_function.check_dimensions(normVmData) == 1:
        input_data = np.array(normVmData, dtype=float)
        input_data = input_data.reshape(1, len(input_data))
        if model.code == constants.TORCH:
            input_data = torch.from_numpy(input_data).float()
    else:
        if model.code == constants.KERAS: 
            input_data = [np.array(input_list, dtype=float).reshape(1, len(input_data)) for input_list in normVmData]
        elif model.code == constants.TORCH:
            input_data = [torch.from_numpy(np.array(input_list, dtype=float).reshape(1, len(input_data))).float() for input_list in normVmData]

    y = model.predict(input_data)

    logger.info("model predict completed. result={0}".format(y))
    logger.debug("model execute completed !!")

    return y

if __name__ == '__main__':
  print("start.")
  import platform
  print(platform.python_version())
  import keras
  import tensorflow
  import sklearn_json
  import pandas as pd
  import os
  print(sklearn_json.__version__)

  py_version = platform.python_version()

  datadir = "d:/models/Teat00001_RF"
  model_path = os.path.join(datadir, "Model_1/test_Model_4_0.json")
  model = RandomForestModel(model_path, constants.CLASSIFICATION)

  import pickle
  with open(os.path.join(datadir,"updater_clf.pkl"), "rb") as f:
    X_norm, y_min, y_max, reginfo = pickle.load(f)
  reginfo = reginfo[0]

  y_pred = model.predict(X_norm)
  y_pred = (y_max - y_min) * y_pred + y_min
  y_pred = reginfo[0] * y_pred + reginfo[1]
  pd.DataFrame(y_pred.reshape(-1,1), columns=['Y_pred_executor']).to_csv(os.path.join(datadir,"test.csv"), index=False)

  print(*y_pred.flatten(), sep='\n')

  ####
  # newmodel = RandomForestModel(os.path.join(datadir, "Model_1.json"), constaants.CLASSIFICATION)
  # new_t_pred = newmodel.predict(X_norm.values
  # input_list = [0.5097565656, 0.523423423424, 0.234234 , 0.1]
  # model = KerasModel('d:/models/wc_s01_29.h5')
  # data = np.array(input_list, dtype=fload)
  # data = data.reshape(1, len(input_list))
  # k = model.predict(data)
  
  
  ####
  # model = TorchModel('d:/models/fnn_dim.pt')
  # normVmData = [1,2,3,4,5]
  # result = execute_model(model, normVmData)
  # print(result)
  
  # model1 = LightGBMModel('d:/models/test1.model')
  # model2 = XGBoostModel('d:/models/test2.model')
  
  # modelList = [model1,model2]
  # X = np.array([0.1,0.2,0.3,0.4,0.5]).reshape([1,-1])
  # form model in modelList:
  #   yhat = model.Predict(X)
  #   print(yhat)