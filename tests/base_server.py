import datetime
import os
import sys
import json
import pprint

import jwt
from flask import current_app
from flask_testing import TestCase
from json import JSONDecodeError
from os.path import join
from app import create_app, db

if sys.version_info < (3, 6):
    json_loads = lambda s: json_loads(s.decode("utf-8")) if isinstance(s, bytes) else json.loads(s)
else:
    json_loads = json.loads


def make_auth_headers(username=None):
    if username is None:
        return {}

    from app.models import User
    user = User.query.filter(User.username == username).first()

    token = jwt.encode({
        'sub': user.email,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=20)},
        current_app.config['SECRET_KEY'])

    headers = {
        'content-type': 'application/json',
        'Authorization': "Bearer {}".format(token)
    }
    return headers

class TestBaseServer(TestCase):

    def setUp(self):
        with self.app.app_context():
            self.clear_data()
            self.load_fixtures()

    def create_app(self):
        from app.api.document.facade import DocumentFacade

        _app = create_app(config_name="test", with_hardcoded_prefix=True)
        with _app.app_context():
            if hasattr(current_app, "elasticsearch"):
                _app.elasticsearch.indices.delete(
                    index=DocumentFacade.get_index_name(),
                    ignore=[400, 404]
                )  # delete the index
                _app.elasticsearch.indices.create(
                    index=DocumentFacade.get_index_name(),
                    ignore=[400, 404]
                )  # create the index


            db.create_all()
            self.client = _app.test_client(allow_subdomain_redirects=True)
            self.db = db
            self.url_prefix = _app.config["API_URL_PREFIX"]

            return _app

    def tearDown(self):
        db.session.remove()
        #db.drop_all()

    @staticmethod
    def clear_data():
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

    def load_sql_fixtures(self, fixtures):
        with self.app.app_context(), db.engine.connect() as connection:
            for fixture in fixtures:
                with open(fixture) as f:
                    for _s in f.readlines():
                        trans = connection.begin()
                        connection.execute(_s, multi=True)
                        trans.commit()

    def load_fixtures(self):
        raise NotImplementedError

    def get(self, url, absolute=False, **kwargs):
        if not absolute:
            url = "%s/%s" % (self.url_prefix, url)
        return self.client.get(url, follow_redirects=True, **kwargs)

    def get_with_auth(self, url, auth_username=None, **kwargs):
        return self.get(url, headers=make_auth_headers(auth_username), **kwargs)

    def post(self, url, data, absolute=False, **kwargs):
        if not absolute:
            url = "%s/%s" % (self.url_prefix, url)
        return self.client.post(url, data=json.dumps(data), follow_redirects=True, **kwargs)

    def post_with_auth(self, url, auth_username=None, **kwargs):
        return self.post(url, headers=make_auth_headers(auth_username), **kwargs)

    def put(self, data, url, absolute=False, **kwargs):
        if not absolute:
            url = "%s/%s" % (self.url_prefix, url)
        return self.client.put(url, data=json.dumps(data), follow_redirects=True, **kwargs)

    def put_with_auth(self, url, auth_username=None, **kwargs):
        return self.put(url, headers=make_auth_headers(auth_username), **kwargs)

    def patch(self, url, data, absolute=False, **kwargs):
        if not absolute:
            url = "%s/%s" % (self.url_prefix, url)
        return self.client.patch(url, data=json.dumps(data), follow_redirects=True, **kwargs)

    def patch_with_auth(self, url, auth_username=None, **kwargs):
        return self.patch(url, headers=make_auth_headers(auth_username), **kwargs)

    def delete(self, url, absolute=False, **kwargs):
        if not absolute:
            url = "%s/%s" % (self.url_prefix, url)
        return self.client.delete(url, follow_redirects=True, **kwargs)

    def delete_with_auth(self, url, auth_username=None, **kwargs):
        return self.delete(url, headers=make_auth_headers(auth_username), **kwargs)

    @staticmethod
    def api_query(method, *args, **kwargs):
        r = method(*args, **kwargs)
        if r.data is None:
            return r, r.status, None
        else:
            try:
                data = json_loads(r.data)
            except JSONDecodeError as e:
                data = r.data
            return r, r.status, data

    def api_get(self, *args, **kwargs):
        return TestBaseServer.api_query(self.get_with_auth, *args, **kwargs)

    def api_post(self, *args, **kwargs):
        return TestBaseServer.api_query(self.post_with_auth, *args, **kwargs)

    def api_put(self, *args, **kwargs):
        return TestBaseServer.api_query(self.put_with_auth, *args, **kwargs)

    def api_patch(self, *args, **kwargs):
        return TestBaseServer.api_query(self.patch_with_auth, *args, **kwargs)

    def api_delete(self, *args, **kwargs):
        return TestBaseServer.api_query(self.delete_with_auth, *args, **kwargs)

    # ========================
    # Pagination test methods
    # ========================
    #def check_self(self, url, resource):
    #    url = url.replace("[", "%5B").replace("]", "%5D")
    #    self.assertEqual(resource["links"]["self"], "http://localhost%s/%s" % (self.url_prefix, url))

    def check_first(self, resource):
        if "first" in resource["links"]:
            if resource["links"]["first"] is None:
                if "next" in resource["links"]:
                    r, status, next_resource = self.api_get(resource["links"]["next"], absolute=True)
                    if status == "200":
                        if resource["links"]["first"] == resource["links"]["last"] and \
                                resource["links"]["self"]== resource["links"]["last"]:
                            pass
                        else:
                            self.check_first(next_resource)
            elif resource["links"]["self"] == resource["links"]["first"]:
                if "prev" in resource["links"]:
                    self.assertEqual(None, resource["links"]["prev"])
            else:
                # it is not the first one
                r, status, first_resource = self.api_get(resource["links"]["first"], absolute=True)
                self.assert200(r)
                self.check_first(first_resource)

    def check_last(self, resource):
        if "last" in resource["links"]:
            if resource["links"]["last"] is None:
                if "prev" in resource["links"]:
                    r, status, prev_resource = self.api_get(resource["links"]["prev"], absolute=True)
                    if status == "200":
                        if resource["links"]["first"] == resource["links"]["last"] and \
                                resource["links"]["self"] == resource["links"]["last"]:
                            pass
                        else:
                            self.check_last(prev_resource)
            elif resource["links"]["self"] == resource["links"]["last"]:
                if "next" in resource["links"]:
                    self.assertEqual(None, resource["links"]["next"])
            else:
                r, status, last_resource = self.api_get(resource["links"]["last"], absolute=True)
                self.assert200(r)
                self.check_last(last_resource)

    def check_next(self, resource):
        if "next" in resource["links"]:
            if resource["links"]["next"] is None:
                if "prev" in resource["links"]:
                    r, status, prev_resource = self.api_get(resource["links"]["prev"], absolute=True)
                    if status == "200":
                        self.check_next(prev_resource)
            else:
                r, status, next_resource = self.api_get(resource["links"]["next"], absolute=True)
                self.assert200(r)
                if "prev" in next_resource["links"]:
                    self.assertIn(next_resource["links"]["prev"], (resource["links"]["self"], resource["links"]["self"]+"&page%5Bnumber%5D=1") )

    def check_prev(self, resource):
        if "prev" in resource["links"]:
            if resource["links"]["prev"] is None:
                if "next" in resource["links"]:
                    r, status, next_resource = self.api_get(resource["links"]["next"], absolute=True)
                    if status == "200":
                        self.check_prev(next_resource)
            else:
                r, status, prev_resource = self.api_get(resource["links"]["prev"], absolute=True)
                self.assert200(r)
                if "prev" in prev_resource["links"]:
                    self.assertEqual(resource["links"]["self"], prev_resource["links"]["next"])

    def _test_pagination_links(self, url):
        r, status, resource = self.api_get(url)
        self.assert200(r)
        if "links" in resource:
            #self.check_self(url, resource)
            self.check_first(resource)
            self.check_last(resource)
            self.check_prev(resource)
            self.check_next(resource)

    def search(self, index, query):
        search_url = "search?index={0}&query={1}".format(index, query)
        r, status, resource = self.api_get(search_url)
        self.assert200(r)
        return resource
