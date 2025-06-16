import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import config.config as config
hq_dbInfo = "oracle+cx_oracle://%s:%s@%s/?encoding=UTF-8&nencoding=UTF-8" % (
    config.hq['username'], config.hq['password'], config.hq['serviceName'])
pt_dbInfo = "oracle+cx_oracle://%s:%s@%s/?encoding=UTF-8&nencoding=UTF-8" % (
    config.pt['username'], config.pt['password'], config.pt['serviceName'])
hq_engine = create_engine(hq_dbInfo, echo=False, pool_size=20, pool_recycle=500, max_overflow=10)
pt_engine = create_engine(pt_dbInfo, echo=False, pool_size=20, pool_recycle=500, max_overflow=10)
hq_db_conn = hq_engine.raw_connection
pt_db_conn = pt_engine.raw_connection
fdry_hq_dbInfo = "oracle+cx_oracle://%s:%s@%s/?encoding=UTF-8&nencoding=UTF-8" % (
    config.fdry_hq['username'], config.fdry_hq['password'], config.fdry_hq['serviceName'])
fdry_pt_dbInfo = "oracle+cx_oracle://%s:%s@%s/?encoding=UTF-8&nencoding=UTF-8" % (
    config.fdry_pt['username'], config.fdry_pt['password'], config.fdry_pt['serviceName'])
fdry_hq_engine = create_engine(fdry_hq_dbInfo, echo=False, pool_size=3, pool_recycle=500, max_overflow=10)
fdry_pt_engine = create_engine(fdry_pt_dbInfo, echo=False, pool_size=3, pool_recycle=500, max_overflow=10)
fdry_hq_db_conn = fdry_hq_engine.raw_connection
fdry_pt_db_conn = fdry_pt_engine.raw_connection
Base = declarative_base()