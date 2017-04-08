# coding: utf-8


import pickle


def get_index_table_name(cls, index):
    if isinstance(index, basestring):
        table_name = "index_" + cls.__name__.lower() + "_" + index
    else:
        table_name = "index_" + cls.__name__.lower() + "_" + "_".join(index)
    return table_name


def create_index(cls, fields):
    """Create indexes for Document"""
    table_name = get_index_table_name(cls, fields)
    query = """CREATE TABLE IF NOT EXISTS {} (
        id TEXT NOT NULL,
        value BLOB NOT NULL
    )""".format(table_name)
    cursor = cls.connection.cursor()
    cursor.execute(query)
    index_query = """CREATE INDEX IF NOT EXISTS
        {table_name}_sqlite_index ON {table_name}(value);
    """.format(table_name=table_name)
    cursor.execute(index_query)
    cls.connection.commit()


def serialize_for_index(value, serializer=pickle):
    """Serializes value for storing it in the index table.
    If value is an iterable we will convert it to tuple because thats how we
    store values for compound indexes.
    """
    if isinstance(value, (list, set, dict)):
        value = tuple(value)
    return serializer.dumps(value)
