from flask import current_app

from app import db


class JSONAPIAbstractFacade(object):

    """

    """
    TYPE = "ABSTRACT-TYPE"
    TYPE_PLURAL = "ABSTRACT-TYPE-PLURAL"

    ITEMS_PER_PAGE = 1000 #TODO: au delà il faut passer par l'api scroll d'elastic search

    def __init__(self, url_prefix, obj, with_relationships_links=True, with_relationships_data=True):
        self.obj = obj
        self.url_prefix = url_prefix
        self.with_relationships_data = with_relationships_data
        self.with_relationships_links = with_relationships_links

        self.self_link = "{url_prefix}/{type_plural}/{id}".format(
            url_prefix=self.url_prefix, type_plural=self.TYPE_PLURAL, id=self.id
        )

        self.resource_identifier = {
            "type": self.TYPE,
            "id": self.id
        }

        self._links_template = {
            "self": "{url_prefix}/{source_col}/{source_id}/relationships".format(
                    url_prefix=self.url_prefix, source_col=self.TYPE_PLURAL, source_id=self.id
            ),
            "related": "{url_prefix}/{source_col}/{source_id}".format(
                    url_prefix=self.url_prefix, source_col=self.TYPE_PLURAL, source_id=self.id
            )
        }

        self.relationships = {}

    @property
    def id(self):
        raise NotImplementedError

    def bind_facade(self):
        raise NotImplementedError

    @property
    def resource(self):
        raise NotImplementedError

    @classmethod
    def get_index_name(cls):
        return "{prefix}__{env}__{index_name}".format(
            prefix=current_app.config.get("INDEX_PREFIX", ""),
            env=current_app.config.get("ENV"),
            index_name=cls.TYPE
        )

    @property
    def meta(self):
        return {}

    @staticmethod
    def make_resource_identifier(id, type):
        return {"id": id, "type": type}

    @staticmethod
    def get_resource_facade(*args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def get_facade(url_prefix, obj, facade_type="default", **kwargs):
        from app.api.facade_manager import JSONAPIFacadeManager
        facade_class = JSONAPIFacadeManager.get_facade_class(obj, facade_type=facade_type)
        e = facade_class(url_prefix, obj, **kwargs)
        kwargs = {}
        errors = []
        return e, kwargs, errors

    @staticmethod
    def post_resource(model, obj_id, attributes, related_resources):
        """
        Instantiate the obj but do not commit it
        :param model:
        :param obj_id:
        :param attributes:
        :param related_resources:
        :return:
        """
        #print("POSTING RESOURCE:", obj_id, attributes, related_resources)
        for att in attributes.keys():
            attributes[att.replace("-", "_")] = attributes.pop(att)

        attributes["id"] = obj_id
        #print("  setting attr", attributes)
        resource = model(**attributes)

        # set related resources
        for rel_name, rel_data in related_resources.items():
            rel_name = rel_name.replace("-", "_")
            #print("  setting rel", rel_name, rel_data)
            if hasattr(resource, rel_name):
                try:
                    setattr(resource, rel_name, rel_data)
                except Exception as e:
                    if len(rel_data) == 0:
                        setattr(resource, rel_name, None)
                    else:
                        setattr(resource, rel_name, rel_data[0])
        return resource

    @staticmethod
    def create_resource(model, obj_id, attributes, related_resources):
        errors = None
        resource = None
        try:
            #print("CREATING RESOURCE:", model, obj_id, attributes, related_resources)
            resource = JSONAPIAbstractFacade.post_resource(model, obj_id, attributes, related_resources)
            db.session.add(resource)
            db.session.commit()
        except Exception as e:
            print(e)
            errors = {
                "status": 403,
                "title": "Error creating resource with data: %s" % str([attributes, related_resources]),
                "detail": str(e)
            }
            db.session.rollback()

        return resource, errors

    # noinspection PyArgumentList
    @staticmethod
    def patch_resource(obj, obj_type, attributes, related_resources, append):
        """
        Update the obj but do not commit it
        :param append:
        :param obj:
        :param obj_type:
        :param attributes:
        :param related_resources:
        :return:
        """
        #print("UPDATING RESOURCE:", obj, obj_type, attributes, related_resources)
        # update attributes
        for att, att_value in attributes.items():
            att_name = att.replace("-", "_")
            #print("  setting attr", att, att_value)
            if hasattr(obj, att_name):
                setattr(obj, att_name, att_value)
            else:
                raise AttributeError("Attribute %s does not exist" % att_name)

        # update related resources
        for rel_name, rel_data in related_resources.items():
            rel_name = rel_name.replace("-", "_")
            #print("  setting rel", rel_name, rel_data)
            if hasattr(obj, rel_name):
                #print(getattr(obj, rel_name))
                # append (POST) or replace (PATCH) replace related resources ?
                if not append:
                    try:
                        setattr(obj, rel_name, rel_data)
                    except Exception:
                        setattr(obj, rel_name, rel_data[0])
                else:
                    try:
                        setattr(obj, rel_name, getattr(obj, rel_name, []) + rel_data)
                    except Exception:
                        setattr(obj, rel_name, getattr(obj, rel_name, []) + rel_data[0])
            else:
                raise AttributeError("Relationship %s does not exist" % rel_name)
        return obj

    @staticmethod
    def update_resource(obj, obj_type, attributes, related_resources, append=False):
        errors = None
        resource = None
        try:
            if obj is None:
                raise Exception("Object is None")
            resource = JSONAPIAbstractFacade.patch_resource(obj, obj_type, attributes, related_resources, append)
            db.session.add(resource)
            db.session.commit()
        except Exception as e:
            print(e)
            errors = {
                "status": 404 if obj is None else 403,
                "title": "Error updating resource '%s' with data: %s" % (
                    obj_type, str([id, attributes, related_resources, append])),
                "detail": str(e)
            }
            db.session.rollback()
        return resource, errors

    @staticmethod
    def delete_resource(obj):
        errors = None
        try:
            if obj is None:
                raise ValueError("Resource does not exist")
            print("DELETING RESOURCE:", obj)
            db.session.delete(obj)
            db.session.commit()
        except Exception as e:
            errors = {
                "status": 404 if obj is None else 403,
                "title": "Cannot delete the resource",
                "detail": str(e)
            }
            db.session.rollback()
        return errors

    def get_related_resource_identifiers(self, facade_class, rel_field, to_many=False, decorators=()):
        def func():
            field = getattr(self.obj, rel_field)
            if to_many:
                return [] if field is None else [
                    facade_class.make_resource_identifier(f.id, facade_class.TYPE)
                    for f in field
                ]
            else:
                return None if field is None else facade_class.make_resource_identifier(field.id, facade_class.TYPE)

        # APPLY decorators if any
        for dec in decorators:
            func = dec(func)

        return func

    def get_related_resources(self, facade_class,  rel_field, to_many=False, decorators=()):
        def func():
            field = getattr(self.obj, rel_field)
            if to_many:
                if field is None:
                    return []
                else:
                    return [
                        facade_class(self.url_prefix, rel_obj,
                                     self.with_relationships_links,  self.with_relationships_data).resource
                        for rel_obj in field
                    ]
            else:
                if field is None:
                    return None
                else:
                    return facade_class(self.url_prefix, field,
                                        self.with_relationships_links, self.with_relationships_data).resource

        # APPLY decorators if any
        for dec in decorators:
            func = dec(func)

        return func

    def set_relationships_mode(self, w_rel_links, w_rel_data):
        self.with_relationships_links = w_rel_links
        self.with_relationships_data = w_rel_data

    def _get_links(self, rel_name):
        return {
            "self": "{template}/{rel_name}".format(template=self._links_template["self"], rel_name=rel_name),
            "related": "{template}/{rel_name}".format(template=self._links_template["related"], rel_name=rel_name)
        }

    def get_exposed_relationships(self):
        if self.with_relationships_data:
            return {
                rel_name: {
                    "links": rel["links"],
                    "data": rel["resource_identifier_getter"]()
                }
                for rel_name, rel in self.relationships.items()
            }
        else:
            # do not provide relationship data, provide just the links
            return {
                rel_name: {
                    "links": rel["links"],
                }
                for rel_name, rel in self.relationships.items()
            }

    def get_data_to_index_when_added(self):
        return []

    def get_data_to_index_when_removed(self):
        return []

    def get_relationship_data_to_index(self, rel_name):
        from app.api.facade_manager import JSONAPIFacadeManager
        to_be_reindexed = []
        for doc in getattr(self.obj, rel_name):
            facade = JSONAPIFacadeManager.get_facade_class(doc)
            f_obj, kwargs, errors = facade.get_resource_facade("", id=doc.id)
            to_be_reindexed.extend(
                f_obj.get_data_to_index_when_added()
            )
        return to_be_reindexed

    def add_to_index(self):
        from app.search import SearchableMixin
        for data in self.get_data_to_index_when_added():
            SearchableMixin.add_to_index(index=data["index"], id=data["id"], payload=data["payload"])

    def remove_from_index(self):
        from app.search import SearchableMixin
        for data in self.get_data_to_index_when_added():
            SearchableMixin.remove_from_index(index=data["index"], id=data["id"])

    def reindex(self, op):
        if op in ("insert", "update"):
            self.add_to_index()
        else:
            self.remove_from_index()