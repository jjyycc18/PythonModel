import logging
from common import constants
import json
import platform
import functools
import os
import numpy as np
from numpyencoder import NumpyEncoder

logger = logging.getLogger(__name__)

# class NumpyEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, np.ndarray):
#             return obj.tolist()
#         if isinstance(obj, np.integer):
#             return int(obj)
#         if isinstance(obj, np.floating):
#             return float(obj)
#         return super().default(obj)

python_version = platform.python_version()
if python_version.startswith('3.7.'):
    logger.info('Python 3.7 detected.')
    from multi_version_execute import multi_version_space_model_py37 as multi_version_space_model
else:
    logger.info('Python other version detected.')
    from multi_version_execute import multi_version_space_model_py36 as multi_version_space_model


def execute_multi_version_model(model, input_list):
    result = multi_version_space_model.execute_model(model, input_list)
    return json.dumps(result, cls=NumpyEncoder)


def load_multi_version_model(model_path, model_code, problem_type):
    model = None
    if model_code == constants.KERAS:
        model = multi_version_space_model.KerasModel(model_path)
    elif model_code == constants.XGBOOST:
        model = multi_version_space_model.XGBoostModel(model_path, problem_type=problem_type)
    return model


if __name__ == '__main__':
    print("## testStart !!!! ###")

    import keras
    import tensorflow
    import sklearn_json
    print(keras.__version__)
    print(tensorflow.__version__)
    print(sklearn_json.__version__)
