from app import db
from app.api.abstract_facade import JSONAPIAbstractFacade
from app.models import Collection


class CollectionFacade(JSONAPIAbstractFacade):
    """

    """
    TYPE = "collection"
    TYPE_PLURAL = "collections"

    @property
    def id(self):
        return self.obj.id

    @staticmethod
    def get_resource_facade(url_prefix, id, **kwargs):
        e = Collection.query.filter(Collection.id == id).first()
        if e is None:
            kwargs = {"status": 404}
            errors = [{"status": 404, "title": "Collection %s does not exist" % id}]
        else:
            e = CollectionFacade(url_prefix, e, **kwargs)
            kwargs = {}
            errors = []
        return e, kwargs, errors

    @property
    def resource(self):
        resource = {
            **self.resource_identifier,
            "attributes": {
                "title": self.obj.title,
                "description": self.obj.description
            },
            "meta": self.meta,
            "links": {
                "self": self.self_link
            }
        }

        if self.with_relationships_links:
            resource["relationships"] = self.get_exposed_relationships()

        return resource

    def __init__(self, *args, **kwargs):
        super(CollectionFacade, self).__init__(*args, **kwargs)
        """Make a JSONAPI resource object describing what is a Collection
        """

        from app.api.document.facade import DocumentFacade
        self.relationships = {
            "documents": {
                "links": self._get_links(rel_name="documents"),
                "resource_identifier_getter": self.get_related_resource_identifiers(DocumentFacade, "documents", to_many=True),
                "resource_getter": self.get_related_resources(DocumentFacade, "documents", to_many=True),
            },
        }