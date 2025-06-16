import requests
from http import HTTPStatus
import json
import logging
logger = logging.getLogger(__name__)
class HttpRequestClient:
    def __init__(self, url, param_dict, timeout=60*30):
        self._url = url
        self._parameters = json.dumps(param_dict)
        self._timeout = timeout
    def get_result(self):
        try:
            res = requests.post(self._url, data=self._parameters, headers={'Content-Type': 'application/json'},
                                timeout=self._timeout, proxies={'http': '', 'https': '', 'ftp': ''}, verify=False)
            ## HTTP Code 200 일때만 결과 파싱
            if res.status_code == HTTPStatus.OK:
                return res.json()
            else:
                logger.error('status code: {CODE}, error: {ERROR}'.format(CODE=res.status_code, ERROR=res.text))
                return None
        except Exception as e:
            logger.exception('HttpRequestClient.get_result : unexpected error occurred. ')
            return None