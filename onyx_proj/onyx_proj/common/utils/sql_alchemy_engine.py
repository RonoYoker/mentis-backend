from sqlalchemy import create_engine
from django.conf import settings

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SqlAlchemyEngine(object, metaclass=Singleton):

    def __init__(self):
        self.engines = {}

    def get_connection(self, database):
        if database not in self.engines:
            engine = create_engine(
                f"mysql://{settings.DATABASES[database]['USER']}:{settings.DATABASES[database]['PASSWORD']}@"
                f"{settings.DATABASES[database]['HOST']}:{settings.DATABASES[database]['PORT']}/{settings.DATABASES[database]['NAME']}",
                echo=True, pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=3600)
            self.engines[database] = engine

        return self.engines[database]


