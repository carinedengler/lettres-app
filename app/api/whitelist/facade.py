from app import db
from app.api.abstract_facade import JSONAPIAbstractFacade
from app.models import Whitelist


class WhitelistFacade(JSONAPIAbstractFacade):
    """

    """
    TYPE = "whitelist"
    TYPE_PLURAL = "whitelists"

    @property
    def id(self):
        return self.obj.id

    @staticmethod
    def get_resource_facade(url_prefix, id, **kwargs):
        e = Whitelist.query.filter(Whitelist.id == id).first()
        if e is None:
            kwargs = {"status": 404}
            errors = [{"status": 404, "title": "whitelist %s does not exist" % id}]
        else:
            e = WhitelistFacade(url_prefix, e, **kwargs)
            kwargs = {}
            errors = []
        return e, kwargs, errors

    def get_documents_resource_identifiers(self):
        from app.api.document.facade import DocumentFacade
        return [] if self.obj.documents is None else [
            DocumentFacade.make_resource_identifier(e.id, DocumentFacade.TYPE)
            for e in self.obj.documents]

    def get_documents_resources(self):
        from app.api.document.facade import DocumentFacade
        return [] if self.obj.documents is None else [DocumentFacade(self.url_prefix, e,
                                                                     self.with_relationships_links,
                                                                     self.with_relationships_data).resource
                                                      for e in self.obj.documents]

    def get_users_resource_identifiers(self):
        from app.api.user.facade import UserFacade
        return [] if self.obj.users is None else [
            UserFacade.make_resource_identifier(e.id, UserFacade.TYPE)
            for e in self.obj.users]

    def get_users_resources(self):
        from app.api.user.facade import UserFacade
        return [] if self.obj.users is None else [UserFacade(self.url_prefix, e,
                                                             self.with_relationships_links,
                                                             self.with_relationships_data).resource
                                                  for e in self.obj.users]

    def __init__(self, *args, **kwargs):
        super(WhitelistFacade, self).__init__(*args, **kwargs)
        """Make a JSONAPI resource object describing what is a whitelist
        """

        self.relationships = {
            "users": {
                "links": self._get_links(rel_name="users"),
                "resource_identifier_getter": self.get_users_resource_identifiers,
                "resource_getter": self.get_users_resources,
                "resource_attribute": "users"
            },
            "documents": {
                "links": self._get_links(rel_name="documents"),
                "resource_identifier_getter": self.get_documents_resource_identifiers,
                "resource_getter": self.get_documents_resources,
                "resource_attribute": "documents"
            },
        }
        self.resource = {
            **self.resource_identifier,
            "attributes": {
                "label": self.obj.label,
            },
            "meta": self.meta,
            "links": {
                "self": self.self_link
            }
        }

        if self.with_relationships_links:
            self.resource["relationships"] = self.get_exposed_relationships()
