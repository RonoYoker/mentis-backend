from datetime import datetime, timedelta

from sqlalchemy import inspect, TIMESTAMP, text,  Column, Integer, String, ForeignKey, DateTime, \
    Time, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class Orm_helper():
    def __init__(self, data={}):
        for c in inspect(self).mapper.column_attrs:
            setattr(self, c.key, data.get(c.key))

    def _asdict(self, extra_attrs=[]):
        ins = inspect(self)
        columns = set(ins.mapper.column_attrs.keys()).difference(ins.expired_attributes).difference(ins.unloaded)
        relationships = set(ins.mapper.relationships.keys()).difference(ins.expired_attributes).difference(ins.unloaded)
        data = {c: getattr(self, c) for c in columns}
        if extra_attrs and len(extra_attrs) > 0:
            for attr in extra_attrs:
                if getattr(self, attr, None) is not None:
                    data[attr] = getattr(self, attr)
        for key in relationships:
            if getattr(self, key) is None:
                data.update({key: None})
            elif isinstance(getattr(self, key), list):
                data.update({key: [obj._asdict() for obj in getattr(self, key)]})
            else:
                data.update({key: getattr(self, key)._asdict()})
        return data