from app import db
from app.api.abstract_facade import JSONAPIAbstractFacade
from app.models import Institution


class InstitutionFacade(JSONAPIAbstractFacade):
    """

    """
    TYPE = "institution"
    TYPE_PLURAL = "institutions"

    @property
    def id(self):
        return self.obj.id

    @staticmethod
    def get_resource_facade(url_prefix, id, **kwargs):
        e = Institution.query.filter(Institution.id == id).first()
        if e is None:
            kwargs = {"status": 404}
            errors = [{"status": 404, "title": "institution %s does not exist" % id}]
        else:
            e = InstitutionFacade(url_prefix, e, **kwargs)
            kwargs = {}
            errors = []
        return e, kwargs, errors

    def get_document_resource_identifiers(self):
        from app.api.document.facade import DocumentFacade
        return [] if self.obj.documents is None else [
            DocumentFacade.make_resource_identifier(c.id, DocumentFacade.TYPE)
            for c in self.obj.documents
        ]

    def get_document_resources(self):
        from app.api.document.facade import DocumentFacade
        return [] if self.obj.documents is None else [
            DocumentFacade(self.url_prefix, c, self.with_relationships_links, self.with_relationships_data).resource
            for c in self.obj.documents
        ]

    def __init__(self, *args, **kwargs):
        super(InstitutionFacade, self).__init__(*args, **kwargs)
        """Make a JSONAPI resource object describing what is an institution
        """

        self.relationships = {
            "documents": {
                "links": self._get_links(rel_name="documents"),
                "resource_identifier_getter": self.get_document_resource_identifiers,
                "resource_getter": self.get_document_resources,
                "resource_attribute": "documents"
            },
        }
        self.resource = {
            **self.resource_identifier,
            "attributes": {
                "name": self.obj.name,
                "ref": self.obj.ref
            },
            "meta": self.meta,
            "links": {
                "self": self.self_link
            }
        }

        if self.with_relationships_links:
            self.resource["relationships"] = self.get_exposed_relationships()
