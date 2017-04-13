# coding: utf-8


from types import MethodType
from .document import Document, Field


def view(method):
    return ViewFunction(method)


class ResultDocument(Document):
    """Result of a view function computation"""
    indexes = "type", ["type", "view_name"]
    type = Field()
    view_name = Field()
    value = Field()


class ViewFunction(object):
    """Wrapper for view functions.
    Store computations as ResultDocument instances, so we can make previous
    results available to the view function itself.
    """
    def __init__(self, func):
        """Store decorated func. We will set self.type once we are bound to an
        instance.
        """
        self.func = func
        self.type = None
        self.is_view_function = True

    def __call__(self, instance):
        """Call self.func passing the collection of documents and the previous
        computation result if any.
        """
        docs = self.type.find_all()
        class_name = self.type.__name__
        view_name = self.func.__name__

        previous_result = self.latest()

        value = self.func(instance, docs, previous_result=previous_result)
        result_document = ResultDocument(value=value, type=class_name, view_name=view_name)
        result_document.save()
        return value

    def __get__(self, instance, type):
        """Bind this callable to an instance"""
        self.type = type
        return MethodType(self, instance, type)

    def latest(self):
        """Return latest computation"""
        class_name = self.type.__name__
        view_name = self.func.__name__
        result = ResultDocument.find_latest(["type", "view_name"], [class_name, view_name])
        if result:
            return result.value

    def history(self):
        """Return all the computations"""
        class_name = self.type.__name__
        view_name = self.func.__name__
        results = ResultDocument.find(["type", "view_name"], [class_name, view_name])
        return (r.value for r in results)
