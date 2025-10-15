space_db_if_service = {
    "bigdataquery_getdata" : "http://127.0.0.1:8075/bigdataquery/getdata",
    "bigdataquery_getdata_sql_mem" : "http://127.0.0.1:8076/bigdataquery/getdataBysql",
    "bigdataquery_getdata_sql_fdry" : "http://127.0.0.1:8077/bigdataquery/getdataBysql"
}    

multi_version_executor = {
    "PY36": "http://127.0.0.1:7001",
    "PY37": "http://127.0.0.1:7002",
    "PY38": "http://127.0.0.1:7003"
}

gpu_executor = {
    "PY36": "http://127.0.0.1:8001",
    "PY37": "http://127.0.0.1:8002",
    "PY38": "http://127.0.0.1:8003"
}

most_executor = {"url": "http://127.0.0.1:7007"}

moonshot_image = {
    "image_api_url": "http://127.0.0.1:9001/api/image",
    "result_api_url": "http://127.0.0.1:9001/api/result",
    "top_result_api_url": "http://127.0.0.1:9001/api/top_result",
    "download_path": "/tmp/moonshot_download",
    "result_path": "/tmp/moonshot_result",
    "delete_path": "/tmp/moonshot_old"
}

redis = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "max_connections": 50,
    "ttl": 600,
    "no_data_ttl": 300
}

gp = {
    "host": "localhost",
    "port": 5432,
    "dbname": "test",
    "username": "test",
    "password": "test"
}

hq = {
    "host": "localhost",
    "port": 1621,
    "username": "hq",
    "password": "test",
    "serviceName": "HQDB"
}

fdry_hq = {
    "host": "localhost",
    "port": 1621,
    "username": "fdry_hq",
    "password": "test",
    "serviceName": "FDRY_HQDB"
}

pt = {
    "host": "localhost",
    "port": 1621,
    "username": "pt",
    "password": "test",
    "serviceName": "PTDB"
}

fdry_pt = {
    "host": "localhost",
    "port": 1621,
    "username": "fdry_pt",
    "password": "test",
    "serviceName": "FDRY_PTDB"
}

delete_job = {
    "trigger_type": "cron",
    "trigger_time": 8,
    "retention_period": 30
}

mp = {
    "url": "http://localhost:8071/executeMp",
    "timeout": 3000
}
