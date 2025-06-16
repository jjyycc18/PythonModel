from dao import vm_dao
from common import constants
from config import config
import requests
import json
import logging

logger = logging.getLogger(__name__)

class HttpRequestClient:
    def __init__(self, url, param_dict, timeout=60):
        self.url = url
        self.param_dict = param_dict
        self.timeout = timeout

    def get_result(self):
        try:
            response = requests.post(self.url, json=self.param_dict, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {str(e)}")
            return None

def get_multi_version_url(version):
    if version in config.multi_version_executor:
        return config.multi_version_executor[version]
    return None

def generate_root_lot_id(lot_id):
  site = vm_dao.get_site_info()
  if '.' in lot_id:
    root_lot_id = lot_id[:6]
    return root_lot_id
  else:
    return lot_id