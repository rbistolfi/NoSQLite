# NoSQLite

Super simple NoSql on top of SQLite written in Python, inspired by
http://backchannel.org/blog/friendfeed-schemaless-mysql


    from nosqlite import init, Document, Field


    init("/tmp/test.db")


    class Movie(Document):
        indexes = ["director"]
        name = Field()
        director = Field()


    sw1 = Movie(name="Star Wars, A New Hope", director="Lucas")
    sw1.save()
    sw2 = Movie(name="Star Wars, The Empire Strikes Back", director="Lucas")
    sw2.save()
    lotr = Movie(name="Lord Of The Rings, The Return of the King", director="Jackson")
    lotr.save()

    lucas_movies = Movie.find("director", "Lucas")


## License

MIT 


## Author

Rodrigo Bistolfi <rbistolfi@gmail.com>
