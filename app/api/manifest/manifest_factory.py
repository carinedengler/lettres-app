import datetime
import json
import os
import pathlib

import requests
from flask import current_app, request
from operator import attrgetter

from app.api.document.facade import DocumentFacade
from app.api.witness.facade import WitnessFacade


dir = pathlib.Path(__file__).parent.resolve()

class ManifestFactory(object):

    MANIFEST_TEMPLATE_FILENAME =  dir / "manifest_template.json"
    COLLECTION_TEMPLATE_FILENAME = dir / "collection_template.json"

    CACHED_MANIFESTS = {

    }

    CACHE_DURATION = 10      # cache manifests (in seconds)
    CACHE_ENTRY_MAX = 150    # how many manifests to cache

    def __init__(self):
        with open(ManifestFactory.MANIFEST_TEMPLATE_FILENAME, 'r') as f:
            self.manifest_template = json.load(f)
        with open(ManifestFactory.COLLECTION_TEMPLATE_FILENAME, 'r') as f:
            self.collection_template = json.load(f)

    def make_collection(self, doc):
        f_obj, errors, kwargs = DocumentFacade.get_facade('', doc)
        collection_url = f_obj.get_iiif_collection_url()
        collection = dict(self.collection_template)

        manifest_urls = []
        for witness in sorted(doc.witnesses, key=attrgetter('num')):
            f_obj, errors, kwargs = WitnessFacade.get_facade('', witness)
            manifest_url = f_obj.get_iiif_manifest_url()
            if manifest_url is not None and (manifest_url, witness) not in manifest_urls:
                manifest_urls.append((manifest_url, witness))

        collection["@id"] = collection_url
        collection["manifests"] = []
        for i, (url, witness) in enumerate(manifest_urls):
            manifest = {
                "@id": url,
                "@type": "sc:Manifest",
                "label": witness.content
            }
            collection["manifests"].append(manifest)

        return collection, collection_url

    def make_manifest(self, witness):
        api_prefix_url = request.host_url[:-1] + current_app.config['API_URL_PREFIX']

        f_obj, errors, kwargs = WitnessFacade.get_facade('', witness)
        manifest_url = f_obj.get_iiif_manifest_url()

        manifest = dict(self.manifest_template)

        # ==== manifest @id
        manifest["@id"] = manifest_url
        # ==== manifest related
        manifest["related"] = f"{api_prefix_url}/documents/{witness.document_id}"

        # === manifest label
        manifest["label"] = witness.content

        # ==== sequence @id
        seq = f"{manifest_url}/sequence/normal"
        manifest["sequences"][0]["@id"] = seq

        # ==== canvases
        if witness.images is None:
            witness.images = []
        ordered_images = [i for i in witness.images]
        ordered_images.sort(key=lambda i: i.order_num)
        # group images by manifest url
        grouped_images = {}
        for img in ordered_images:
            # /!\ maybe tied to the manifest url naming scheme in Gallica
            #url = img.canvas_id.rsplit("/", maxsplit=2)[0]
            orig_manifest_url = "{url}/manifest.json".format(url=img.canvas_id)

            if orig_manifest_url not in grouped_images:
                grouped_images[orig_manifest_url] = []

            grouped_images[orig_manifest_url].append(img.canvas_id)

        # fetching canvases from manifests
        canvases = []
        fetch_canvas = current_app.manifest_factory.fetch_canvas
        for orig_manifest_url, canvas_ids in grouped_images.items():
            new_canvases = fetch_canvas(orig_manifest_url, canvas_ids, cache=False)
            canvases.extend(new_canvases)

        manifest["sequences"][0]["canvases"] = canvases

        return manifest, manifest_url

    @classmethod
    def _fetch(cls, manifest_url):
        r = requests.get(manifest_url)
        #print("fetching... %s" % manifest_url, end=" ", flush=True)
        manifest = r.json()
        #print(r.status_code)
        return manifest

    @classmethod
    def _get_from_cache(cls, manifest_url):
        if manifest_url not in cls.CACHED_MANIFESTS.keys():
            try:
                manifest = cls._fetch(manifest_url)
            except Exception as e:
                print("cannot get manifest", manifest_url)
                manifest = {}
            # CACHE 10 MANIFESTS MAX
            if len(cls.CACHED_MANIFESTS.keys()) >= cls.CACHE_ENTRY_MAX:
                l = [(dt, url) for url, (_, dt) in cls.CACHED_MANIFESTS.items()]
                l.sort(reverse=True)
                oldest_cached_url = l[0][1]
                cls.CACHED_MANIFESTS.pop(oldest_cached_url)
                #print("popped", oldest_cached_url)
            #print("caching", manifest_url)
            cls.CACHED_MANIFESTS[manifest_url] = (manifest, datetime.datetime.now())
            #print("nb cache entries:", len(cls.CACHED_MANIFESTS.keys()))
            return manifest
        else:
            manifest, dt = cls.CACHED_MANIFESTS[manifest_url]
            #print("get from cache")
            # refresh the cache entry
            duration = datetime.datetime.now() - dt
            if duration.total_seconds() > cls.CACHE_DURATION:
                cls.CACHED_MANIFESTS.pop(manifest_url)
                #print("refresh cache entry")
                return cls._get_from_cache(manifest_url)
            else:
                # extending cache duration
                cls.CACHED_MANIFESTS[manifest_url] = (manifest, datetime.datetime.now())
                return manifest

    @classmethod
    def fetch_canvas(cls, manifest_url, canvas_ids, cache=False):
        if cache:
            manifest = cls._get_from_cache(manifest_url)
        else:
            manifest = cls._fetch(manifest_url)

        try:
            canvases = [canvas for canvas in manifest["sequences"][0]["canvases"]
                    if canvas["@id"] in canvas_ids if "sequences" in manifest]
        except KeyError:
            canvases = []

        return canvases
