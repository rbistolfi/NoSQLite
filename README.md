# NoSQLite

Super simple NoSQL style data store on top of SQLite written in Python, inspired by
http://backchannel.org/blog/friendfeed-schemaless-mysql


    >>> from nosqlite import init, Document, Field
    >>> from nosqlite.view import view


    >>> init("/tmp/test.db")


    >>> class Movie(Document):
    ...    indexes = ["director"]
    ...    name = Field()
    ...    director = Field()
    ...    price = Field()
    ...
    ...    @view
    ...    def count_by_director(self, docs, previous_result=None):
    ...        """View funcs are called on save"""
    ...        if previous_result is None:
    ...            return {self.director: 1}
    ...        else:
    ...            prev = previous_result.get(self.director, 0)
    ...            previous_result[self.director] = prev + 1
    ...            return previous_result


    >>> sw1 = Movie(name="Star Wars, A New Hope", director="Lucas", price=19.99)
    >>> sw1.save()
    >>> sw2 = Movie(name="Star Wars, The Empire Strikes Back", director="Lucas", price=99.99)
    >>> sw2.save()
    >>> lotr = Movie(name="Lord Of The Rings, The Return of the King", director="Jackson", price=99.99)
    >>> lotr.save()

    >>> lucas_movies = Movie.find("director", "Lucas")
    >>> for movie in lucas_movies:
    ...     print movie.name
    Star Wars, The Empire Strikes Back
    Star Wars, A New Hope

    >>> Movie.count_by_director.latest()
    {'Jackson': 1, 'Lucas': 2}


## What

* Class based data store
* Attributes marked with `Field()` are saved 
* Data is pickled and stored in SQLite
* "Indexes" are just persistent maps stored in SQLite
* You can only search by indexed fields
* View functions can be used for extra computations


## API

`init(dbname=":memory:")`
    Init store using _dbname_ as SQLite database

`Document`
    Base class for documents

`Document.save()`
    Store fields in SQLite

`Document.delete()`
    Delete document

`Document.find(index, value)`
    Find document 

`Document.find_one(index, value)`
    Find first match

`Document.find_all()`
    You got it :)

`Document.is_new()`
    Returns True if doc has not been saved, False otherwise

`Field`
    Mark an attribute in a document for being saved

`view(func)`
    Declare a method of a Document subclass as view function


## License

MIT 


## Author

Rodrigo Bistolfi <rbistolfi@gmail.com>
