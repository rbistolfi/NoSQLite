# coding: utf-8


"""nosqlite - by rbistolfi"""


import sqlite3
import pickle
import uuid
import datetime


_conn = None


def init_data_store(dbconnection):
    query = """CREATE TABLE IF NOT EXISTS entities (
        added_id INTEGER AUTO_INCREMENT PRIMARY KEY,
        id TEXT NOT NULL UNIQUE,
        updated TEXT NOT NULL,
        type TEXT NOT NULL,
        body BLOB
    )
    """
    c = dbconnection.cursor()
    c.execute(query)
    dbconnection.commit()


def init(dbname=':memory:'):
    global _conn
    _conn = sqlite3.connect(dbname)
    init_data_store(_conn)
    return _conn


def get_connection():
    global _conn
    return _conn


def reset_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entities")
    conn.commit()


class DocumentMeta(type):

    def __new__(cls, name, bases, namespace):
        newcls = super(DocumentMeta, cls).__new__(cls, name, bases, namespace)
        newcls.connection = get_connection()
        indexes = namespace.get("indexes", [])
        for name, field in newcls.fields():
            field.name = "__nosqlite_" + name
            if name in indexes:
                cls.create_index(newcls, name, field)
        return newcls

    def create_index(cls, name, field):
        table_name = "index_" + cls.__name__.lower() + "_" + name
        query = """CREATE TABLE IF NOT EXISTS {} (
            id TEXT NOT NULL,
            value {} NOT NULL
        )""".format(table_name, field.db_type)
        cursor = cls.connection.cursor()
        cursor.execute(query)
        cls.connection.commit()

    def remove(cls, id):
        cursor = cls.connection.cursor()
        cursor.execute("DELETE FROM entities WHERE id=?", [id])


class Field(object):
    """Mark something to be saved.
    Uses the name class attribute set by the metaclass for storing the value
    in the object. The `db_type` attribute is set by subclasses and it is used
    for storing the value in the index tables.
    """
    name = None
    db_type = None

    def __get__(self, obj, type=None):
        return getattr(obj, self.name)

    def __set__(self, obj, value, type=None):
        if obj:
            setattr(obj, self.name, value)


class IntegerField(Field):
    db_type = "INTEGER"


class StringField(Field):
    db_type = "TEXT"


class Document(object):

    __metaclass__ = DocumentMeta

    indexes = []

    @classmethod
    def fields(cls):
        for k, v in cls.__dict__.items():
            if isinstance(v, Field):
                yield k, v

    @classmethod
    def find(cls, key=None, value=None):
        if key is None:
            return cls.find_all()
        return cls.find_in_indexed_field(key, value)

    @classmethod
    def create_instances_from_results(cls, results):
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
    def find_all(cls):
        cursor = cls.connection.cursor()
        results = cursor.execute("SELECT * FROM entities WHERE type=?", [cls.__name__])
        instances = cls.create_instances_from_results(results)
        return instances

    @classmethod
    def find_in_indexed_field(cls, field_name, value):
        assert field_name in cls.indexes, "You can only search in indexed columns"
        cursor = cls.connection.cursor()
        table_name = "index_" + cls.__name__.lower() + "_" + field_name
        query = "SELECT * FROM entities WHERE id IN (SELECT id FROM {} WHERE value=?) AND type=?".format(table_name)
        results = cursor.execute(query, [value, cls.__name__])
        instances = cls.create_instances_from_results(results)
        return instances

    @classmethod
    def find_one(cls, key=None, value=None):
        g = cls.find(key=key, value=value)
        return next(g)

    def is_new(self):
        return hasattr(self, "id")

    def save(self):
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
            table_name = "index_" + self.__class__.__name__.lower() + "_" + index
            value = getattr(self, index)
            query = "INSERT INTO {} VALUES (?, ?)".format(table_name)
            cursor.execute(query, [self.id, value])

        self.connection.commit()

    def delete(self):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM entities WHERE id=?", [self.id])
