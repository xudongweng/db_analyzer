from django.conf import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class SQL_Model:
    Base = declarative_base()

    def __init__(self, url):
        self.engine = create_engine(url)

    def reset_url(self, url):
        self.engine = create_engine(url)

    def con_test(self):
        try:
            dbsession = sessionmaker(bind=self.engine)
            session = dbsession()
            rs = session.execute('select 1')
            ds = rs.fetchall()
            session.commit()
            return ds[0][0]
        except Exception as e:
            settings.LOGGER.error(str(e))
            return None

    def query(self, sql):
        try:
            dbsession = sessionmaker(bind=self.engine)
            session = dbsession()
            rs = session.execute(sql)
            ds = rs.fetchall()
            session.commit()
            return ds
        except Exception as e:
            settings.LOGGER.error(str(e))
            return None

    def execute(self, sql):
        try:
            dbsession = sessionmaker(bind=self.engine)
            session = dbsession()
            session.execute(sql)
            rs = session.execute('SELECT LAST_INSERT_ID()')
            ds = rs.fetchall()
            session.commit()
            return ds[0][0]
        except Exception as e:
            settings.LOGGER.error(str(e))
            return None

