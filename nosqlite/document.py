# coding: utf-8


"""nosqlite - by rbistolfi"""


import datetime
import pickle
import uuid

from .db import get_connection
from .index import create_index, get_index_table_name, serialize_for_index


class DocumentMeta(type):
    """Setup Document classes"""

    def __new__(cls, name, bases, namespace):
        """Pass active connection to new Document and create indexes"""
        newcls = super(DocumentMeta, cls).__new__(cls, name, bases, namespace)
        newcls.connection = get_connection()
        newcls.DoesNotExist = type("DoesNotExist", (Exception,), {})
        for name, field in newcls.fields():
            field.name = "__nosqlite_" + name
        indexes = namespace.get("indexes", [])
        for index in indexes:
            create_index(newcls, index)
        return newcls

    def remove(cls, id):
        """Delete document from the db if it matches id"""
        cursor = cls.connection.cursor()
        cursor.execute("DELETE FROM entities WHERE id=?", [id])


class Field(object):
    """Mark something to be saved.
    Uses the name class attribute set by the metaclass for storing the value
    in the object.
    """
    name = None

    def __get__(self, obj, type=None):
        return getattr(obj, self.name)

    def __set__(self, obj, value, type=None):
        if obj:
            setattr(obj, self.name, value)


class Document(object):
    """Base class for documents"""

    __metaclass__ = DocumentMeta

    indexes = []

    @classmethod
    def fields(cls):
        """Fields defined in this document"""
        for k, v in cls.__dict__.items():
            if isinstance(v, Field):
                yield k, v

    @classmethod
    def create_instances_from_results(cls, results):
        """Create instances of this class using db results for initializing it"""
        for added_id, id, updated, klass, body in results:
            instance = cls()
            instance.id = id
            instance.updated = updated

            d = pickle.loads(body)

            for name, field in cls.fields():
                value = d.get(name, None)
                setattr(instance, name, value)

            yield instance

    @classmethod
    def find(cls, index=None, value=None):
        """Find documents matching query. If query is empty, return all
        documents for this type.
        """
        if index is None:
            return cls.find_all()
        return cls.find_in_indexed_field(index, value)

    @classmethod
    def find_all(cls):
        """Return all existing documents"""
        cursor = cls.connection.cursor()
        results = cursor.execute("SELECT * FROM entities WHERE type=?", [cls.__name__])
        instances = cls.create_instances_from_results(results)
        return instances

    @classmethod
    def find_in_indexed_field(cls, index, value):
        """Find items by indexed columns"""
        assert index in cls.indexes, "You can only search in indexed columns"
        cursor = cls.connection.cursor()
        table_name = get_index_table_name(cls, index)
        value = serialize_for_index(value)
        query = "SELECT * FROM entities WHERE id IN (SELECT id FROM {} WHERE value=?) AND type=?".format(table_name)
        results = cursor.execute(query, [value, cls.__name__])
        instances = cls.create_instances_from_results(results)
        return instances

    @classmethod
    def find_one(cls, index=None, value=None):
        """Find the 1st instance matching query"""
        g = cls.find(index, value)
        one = next(g, None)
        if one is None:
            raise cls.DoesNotExist
        return one

    def is_new(self):
        """I have never been saved"""
        return hasattr(self, "id")

    def save(self):
        """Store or updated document in the db"""
        document = {}

        for name, field in self.__class__.fields():
            value = getattr(self, name)
            document[name] = value

        cursor = self.connection.cursor()

        now = datetime.datetime.now().isoformat()
        pickled = pickle.dumps(document)

        if not self.is_new():
            self.id = str(uuid.uuid4())
            self.updated = now
            query = "INSERT INTO entities (id, updated, type, body) VALUES (?, ?, ?, ?)"
            cursor.execute(query, [self.id, self.updated, self.__class__.__name__, pickled])
        else:
            query = "UPDATE entities SET body=?, updated=? WHERE id=?"
            cursor.execute(query, [pickled, now, self.id])

        for index in self.indexes:
            table_name = get_index_table_name(self.__class__, index)
            if isinstance(index, basestring):
                value = getattr(self, index)
            else:
                value = tuple(getattr(self, field) for field in index)
            value = serialize_for_index(value)
            query = "INSERT INTO {} VALUES (?, ?)".format(table_name)
            cursor.execute(query, [self.id, value])

        self.connection.commit()

    def delete(self):
        """Remove this document from the db"""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM entities WHERE id=?", [self.id])
        self.connection.commit()
