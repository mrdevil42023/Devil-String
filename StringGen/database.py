import logging
import os
from datetime import datetime
from urllib.parse import urlparse

from opensearchpy._async.client import AsyncOpenSearch
from opensearchpy import NotFoundError

logger = logging.getLogger(__name__)

OPENSEARCH_URI = os.getenv("OPENSEARCH_URI", "")

INDEX = "users"

_client = None


def get_client() -> AsyncOpenSearch:
    global _client
    if _client is None:
        if not OPENSEARCH_URI:
            raise RuntimeError("OPENSEARCH_URI is not set")
        parsed = urlparse(OPENSEARCH_URI)
        _client = AsyncOpenSearch(
            hosts=[{"host": parsed.hostname, "port": parsed.port or 24832}],
            http_auth=(parsed.username, parsed.password),
            use_ssl=True,
            verify_certs=False,
            ssl_show_warn=False,
        )
    return _client


async def ensure_index():
    client = get_client()
    try:
        exists = await client.indices.exists(index=INDEX)
        if not exists:
            await client.indices.create(
                index=INDEX,
                body={
                    "mappings": {
                        "properties": {
                            "name": {"type": "text"},
                            "username": {"type": "keyword"},
                            "is_bot": {"type": "boolean"},
                            "joined": {"type": "date"},
                        }
                    }
                },
            )
            logger.info(f"Created OpenSearch index: {INDEX}")
    except Exception as e:
        logger.warning(f"ensure_index error: {e}")


class _AsyncFind:
    def __init__(self, filter_dict=None, sort_key=None, sort_dir=-1):
        self._filter = filter_dict
        self._sort_key = sort_key
        self._sort_dir = sort_dir

    def sort(self, key, direction):
        self._sort_key = key
        self._sort_dir = direction
        return self

    def __aiter__(self):
        return self._iter()

    async def _iter(self):
        client = get_client()
        body = {"query": {"match_all": {}}, "size": 10000}
        if self._sort_key:
            order = "desc" if self._sort_dir == -1 else "asc"
            body["sort"] = [{self._sort_key: {"order": order}}]
        try:
            resp = await client.search(index=INDEX, body=body)
            for hit in resp["hits"]["hits"]:
                doc = hit["_source"]
                doc["_id"] = int(hit["_id"])
                yield doc
        except Exception as e:
            logger.warning(f"OpenSearch find error: {e}")


class UsersCollection:
    async def update_one(self, filter_dict, update_dict, upsert=False):
        client = get_client()
        doc_id = str(filter_dict.get("_id"))
        doc = dict(update_dict.get("$set", {}))
        for k, v in doc.items():
            if isinstance(v, datetime):
                doc[k] = v.isoformat()
        try:
            await client.update(
                index=INDEX,
                id=doc_id,
                body={"doc": doc, "doc_as_upsert": upsert},
            )
        except Exception as e:
            raise e

    async def count_documents(self, filter_dict=None):
        client = get_client()
        try:
            resp = await client.count(index=INDEX, body={"query": {"match_all": {}}})
            return resp.get("count", 0)
        except Exception as e:
            logger.warning(f"OpenSearch count error: {e}")
            return 0

    async def find_one(self, filter_dict):
        client = get_client()
        doc_id = str(filter_dict.get("_id"))
        try:
            resp = await client.get(index=INDEX, id=doc_id)
            doc = resp["_source"]
            doc["_id"] = int(resp["_id"])
            return doc
        except NotFoundError:
            return None
        except Exception as e:
            logger.warning(f"OpenSearch find_one error: {e}")
            return None

    def find(self, filter_dict=None, projection=None):
        return _AsyncFind(filter_dict)


users = UsersCollection()
