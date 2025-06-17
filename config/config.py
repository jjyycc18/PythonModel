multi_version_executor = {
    "PY36": "http://127.0.0.1:7001",
    "PY37": "http://127.0.0.1:7002",
    "PY38": "http://127.0.0.1:7003"
}

most_executor = {"url": "http://127.0.0.1:7007"}

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
