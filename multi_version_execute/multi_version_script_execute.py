import logging
logger = logging.getLogger(__name__)

def execute_multi_version_script(script):
  local_dict = {}
  exec(script, local_dict)
  return local_dict
