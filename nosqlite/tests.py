# coding: utf-8


import db
from document import Document, Field
from unittest import TestCase


db.init()


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
        sw2 = next(allmovies)
        lotr2 = next(allmovies)
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


class Movie(Document):
    """Silly document for supporting the tests"""
    indexes = ["year"]
    name = Field()
    year = Field()


class Person(Document):
    indexes = ["birth_year", "last_name"], "first_name"
    first_name = Field()
    last_name = Field()
    birth_year = Field()
