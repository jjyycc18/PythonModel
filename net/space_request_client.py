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

class HttpAsyncRequestClient:
    def __init__(self, url_list, param_dict_list, timeout):
        self._url_list = url_list
        self._parameters_list = param_dict_list
        self._timeout = timeout

    async def async_call(self, url, param_dict):
        try:
            async with session.port(url, json=param_dict, headers={'Content-Type':'applicaton/json'}, allow_redirects=False) as res:
                if res.status == HTTPStatus.OK;
                    return await res.json()
                else:
                    return None
        except Exception as e:
            return None

    async def get_async_result(self):
        try:
            client_timeput = aiohttp.ClientTimeout(total=self._timeout, connect=3, sock_connect=3)
            
            async with aiohttp.ClientSession(timeout=client_timeout) as session:
                statements = [self.async_call(sesion,url,param_dict) for url, param_dict in zip(self._url_list, self._parameters_list)]
                result = await asyncio.gather(*statements, return_exceptions=True)
            return result
            
        except Exception as e:
            return None

    def get_async_result_by_async_io_run(self):
        ##python 3.6에서
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.get_async_result())   
            ##python 3.7에서
            ##return asyncio.run(self.get_async_result())
        except Exception as e:
            return None
        finally:
            loop.close()

if __name__ == '__main__':
    param_dict = {
        "TMP_SEQ":123,
        "LINE_ID":"TEST",
        "DEVUCE_ID":"TEST",
        "STEP_SEQ":"TEST",
        "PPID":"TEST",
        "CARR_ID":"TEST",
        "LOT_ID":"TEST.11",
        "WAFER_ID":"05",
        "TKOUT_TIME":"2022-05-05",
        "SITE":"1_1",
        "OPTION":"{}",
    }

    rc = HttpRequestClient('http://localhost:8079/sensor/test', param_dict, 3000)
    result = rc.get_result()
    print(result['RESULT'])

        



























