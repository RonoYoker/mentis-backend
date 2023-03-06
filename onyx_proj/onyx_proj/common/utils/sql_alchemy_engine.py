from sqlalchemy import create_engine
from django.conf import settings
from urllib.parse import quote
import logging

logger = logging.getLogger("apps")


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SqlAlchemyEngine(object, metaclass=Singleton):

    def __init__(self, **kwargs):
        self.engines = {}
        self.database = kwargs.get("database", "default")
        self.user, self.password = self.get_sql_user_by_project_id()

    def get_connection(self):
        if self.database not in self.engines:
            engine = create_engine(
                f"mysql://{self.user}:%s@"
                f"{settings.DATABASES[self.database]['HOST']}:{settings.DATABASES[self.database]['PORT']}/{settings.DATABASES[self.database]['NAME']}?charset=utf8mb4" % quote(
                    f"{self.password}"),
                echo=True, pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=3600)
            self.engines[self.database] = engine
        return self.engines[self.database]

    def get_sql_user_by_project_id(self):
        """
        returns user password for creating mysql connection to limit access based on project_id
        """
        try:
            return settings.DATABASES[self.database]["USER"], settings.DATABASES[self.database]["PASSWORD"]
        except Exception as e:
            logger.error(f"Exception: {e}. settings: {settings.DATABASES}")
