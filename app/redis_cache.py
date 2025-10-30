import redis
import pandas as pd
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis 연결 설정
redis_host = 'localhost'
redis_port = 6379
redis_db = 0
redis_ttl = 3600  # 1시간

# Redis 연결 풀 생성
redis_pool = redis.ConnectionPool(
    host=redis_host,
    port=redis_port,
    db=redis_db,
    decode_responses=True
)

logger.info("Redis 연결이 초기화되었습니다.")

def save_dataframe_to_redis(key, df):
    """
    DataFrame을 Redis에 저장합니다.
    
    Args:
        key (str): Redis 키
        df (pd.DataFrame): 저장할 DataFrame
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        with redis.StrictRedis(connection_pool=redis_pool) as rd:
            if df is not None and not df.empty:
                # DataFrame을 JSON 문자열로 변환
                df_json = df.to_json(orient='records', date_format='iso')
                rd.set(key, df_json)
                rd.expire(key, redis_ttl)
                return True
            else:
                return False
    except Exception as e:
        logger.exception('redis_cache.save_dataframe_to_redis: unexpected exception is occurred.')
        return False

def load_dataframe_from_redis(key):
    """
    Redis에서 DataFrame을 불러옵니다.
    
    Args:
        key (str): Redis 키
        
    Returns:
        tuple: (DataFrame, ttl) 또는 (None, None)
    """
    try:
        with redis.StrictRedis(connection_pool=redis_pool) as rd:
            data = rd.get(key)
            ttl = rd.ttl(key)
            
            if data:
                # JSON 문자열을 DataFrame으로 변환
                df = pd.read_json(data, orient='records')
                # datetime 컬럼이 있다면 변환
                for col in df.columns:
                    if df[col].dtype == 'object':
                        try:
                            df[col] = pd.to_datetime(df[col], errors='ignore')
                        except:
                            pass
                return df, ttl
            else:
                return None, None
    except Exception as e:
        logger.exception('redis_cache.load_dataframe_from_redis: unexpected exception is occurred.')
        return None, None

def save_string_to_redis(key, value, ttl=None):
    """
    단일 문자열 값을 Redis에 저장합니다.

    Args:
        key (str): Redis 키
        value (str): 저장할 문자열 (None 허용 안함)
        ttl (int, optional): 만료 시간(초). 지정하지 않으면 기본 redis_ttl 사용.

    Returns:
        bool: 저장 성공 여부
    """
    try:
        if value is None:
            return False
        with redis.StrictRedis(connection_pool=redis_pool) as rd:
            rd.set(key, str(value))
            rd.expire(key, ttl if ttl is not None else redis_ttl)
            return True
    except Exception as e:
        logger.exception('redis_cache.save_string_to_redis: unexpected exception is occurred.')
        return False

def load_string_from_redis(key):
    """
    Redis에서 단일 문자열 값을 불러옵니다.

    Args:
        key (str): Redis 키

    Returns:
        tuple: (value:str or None, ttl:int or -2)
            - value: 저장된 문자열 (없으면 None)
            - ttl: key의 TTL (초). 키가 없으면 -2, 만료 없음이면 -1
    """
    try:
        with redis.StrictRedis(connection_pool=redis_pool) as rd:
            value = rd.get(key)
            ttl = rd.ttl(key)
            # rd.get은 decode_responses=True 이므로 이미 str 또는 None 반환
            return value, ttl
    except Exception as e:
        logger.exception('redis_cache.load_string_from_redis: unexpected exception is occurred.')
        return None, None
        
if __name__ == '__main__':
    print() 
