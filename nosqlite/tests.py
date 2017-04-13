# coding: utf-8


import db
db.init(":memory:")  # noqa

from document import Document, Field
from view import view
from unittest import TestCase


class NoSqliteTestCase(TestCase):

    def setUp(self):
        db.reset_database()

    def test_save(self):
        """We can store a document in the database"""
        sw1 = Movie()
        sw1.name = "Star Wars"
        sw1.year = 1981
        sw1.save()

        sw2 = Movie.find_one()

        self.assertEqual(sw1.id, sw2.id)
        self.assertEqual(sw1.updated, sw2.updated)
        self.assertEqual(sw1.name, sw2.name)
        self.assertEqual(sw1.year, sw2.year)

    def test_find(self):
        """We can search the database"""
        sw1 = Movie()
        sw1.name = "Star Wars"
        sw1.year = 1981
        sw1.save()

        lotr1 = Movie()
        lotr1.name = "Lord Of The Rings"
        lotr1.year = 2002
        lotr1.save()

        movies1981 = Movie.find("year", 1981)
        sw2 = next(movies1981)

        self.assertEqual(sw1.id, sw2.id)
        self.assertRaises(StopIteration, next, movies1981)

    def test_find_one(self):
        """We can find a single doc"""
        sw1 = Movie()
        sw1.name = "Star Wars"
        sw1.year = 1981
        sw1.save()

        lotr1 = Movie()
        lotr1.name = "Lord Of The Rings"
        lotr1.year = 2002
        lotr1.save()

        sw2 = Movie.find_one("year", 1981)

        self.assertEqual(sw1.id, sw2.id)

    def test_find_all(self):
        """We can retrieve all the existing documents"""
        sw1 = Movie()
        sw1.name = "Star Wars"
        sw1.year = 1981
        sw1.save()

        lotr1 = Movie()
        lotr1.name = "Lord Of The Rings"
        lotr1.year = 2002
        lotr1.save()

        allmovies = Movie.find_all()
        lotr2 = next(allmovies)
        sw2 = next(allmovies)
        self.assertEqual(sw1.id, sw2.id)
        self.assertEqual(lotr1.id, lotr2.id)
        self.assertRaises(StopIteration, next, allmovies)

    def test_delete(self):
        """We can delete a document"""
        sw1 = Movie()
        sw1.name = "Star Wars"
        sw1.year = 1981
        sw1.save()

        lotr1 = Movie()
        lotr1.name = "Lord Of The Rings"
        lotr1.year = 2002
        lotr1.save()

        lotr1.delete()

        allmovies = Movie.find_all()
        sw2 = next(allmovies)
        self.assertEqual(sw1.id, sw2.id)
        self.assertRaises(StopIteration, next, allmovies)

    def test_compound_index(self):
        """We can search compound indexes"""
        p1 = Person()
        p1.first_name = "Alan"
        p1.last_name = "Kay"
        p1.birth_year = 1971
        p1.save()
        p2 = Person.find_one(["birth_year", "last_name"], [1971, "Kay"])
        self.assertEqual(p1.id, p2.id)

    def test_does_not_exist(self):
        self.assertRaises(Movie.DoesNotExist, Movie.find_one, "year", 1992)

    def test_required(self):
        """Document with missing required fields can't be saved"""
        movie = Movie(year=2012)
        self.assertRaises(TypeError, movie.save)

    def test_default(self):
        """Field defines a default"""
        movie = Movie(name="Blade Runner")
        movie.save()
        movie = Movie.find_one("year", 42)
        self.assertEqual(movie.name, "Blade Runner")
        self.assertEqual(movie.year, 42)

    def test_view(self):
        """Test view functions"""
        for i in range(5):
            n = Product(price=i)
            n.save()
        self.assertEqual(Product.average.latest(), 2.0)
        self.assertEqual(list(Product.average.history()), [2.0, 1.5, 1.0, 0.5, 0.0])


class Movie(Document):
    """Silly document for supporting the tests"""
    indexes = ["year"]
    name = Field(required=True)
    year = Field(default=42)


class Person(Document):
    """Another silly document, this time with compound index"""
    indexes = ["birth_year", "last_name"], "first_name"
    first_name = Field()
    last_name = Field()
    birth_year = Field()


class Product(Document):
    indexes = ["name"]
    name = Field()
    price = Field()

    @view
    def average(self, docs, previous_result=None, is_new=False):
        s = 0.0
        l = 0.0
        for doc in docs:
            s += doc.price
            l += 1
        return s / l
