import json

import sqlalchemy
import sqlalchemy.ext.declarative as declarative

from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.ext.mutable import Mutable

class ToDictBase(object):
    def to_dict(self, include=None, exclude=None, rename={}, childargs={}):
        result = {}
        mapper = sqlalchemy.inspect(self.__class__)

        for column in mapper.column_attrs:
            # regular attrs default to included
            if exclude is None or column.key not in exclude:
                result[rename.get(column.key, column.key)] = getattr(self, column.key)

        for column in mapper.relationships:
            # relationship attrs default to excluded
            if include is not None and column.key in include:
                related_objs = getattr(self, column.key)

                if related_objs is None:
                    related_dict = None
                elif isinstance(related_objs, list):
                    kwargs = childargs.get(column.key, {})
                    related_dict = [o.to_dict(**kwargs) for o in related_objs]
                else:
                    kwargs = childargs.get(column.key, {})
                    related_dict = related_objs.to_dict(**kwargs)

                result[rename.get(column.key, column.key)] = related_dict

        return result

class JsonEncodedImmutable(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

class JsonEncodedList(Mutable, list):
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, JsonEncodedList):
            return value
        else:
            if isinstance(value, list):
                return JsonEncodedList(value)
            else:
                return Mutable.coerce(key, value)

    def append(self, item):
        list.append(item)
        self.changed()

    def __setitem__(self, index, value):
        list.__setitem__(index, value)
        self.changed()

    def __delitem__(self, index):
        list.__delitem__(index)
        self.changed()

Base = declarative.declarative_base(cls=ToDictBase)
