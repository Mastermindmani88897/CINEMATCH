from typing import Any, Dict, List
from bson import ObjectId


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively converts MongoDB document `_id` and BSON ObjectIds.
    Ensures `id` is an integer for compatibility with Pydantic schemas and frontend routing.
    """
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if not isinstance(doc, dict):
        return doc

    res = {}
    for k, v in doc.items():
        if k == "_id":
            res["_id"] = str(v)
            if "id" not in doc or doc["id"] is None:
                if "tmdb_id" in doc and isinstance(doc["tmdb_id"], int):
                    res["id"] = doc["tmdb_id"]
                else:
                    res["id"] = abs(hash(str(v))) % 2147483647 + 1
        elif k == "id":
            if isinstance(v, int):
                res["id"] = v
            elif isinstance(v, str) and v.isdigit():
                res["id"] = int(v)
            elif "tmdb_id" in doc and isinstance(doc["tmdb_id"], int):
                res["id"] = doc["tmdb_id"]
            else:
                res["id"] = abs(hash(str(v))) % 2147483647 + 1
        elif isinstance(v, ObjectId):
            res[k] = str(v)
        elif isinstance(v, dict):
            res[k] = serialize_doc(v)
        elif isinstance(v, list):
            res[k] = [serialize_doc(item) for item in v]
        else:
            res[k] = v

    if "id" not in res:
        if "tmdb_id" in res and isinstance(res["tmdb_id"], int):
            res["id"] = res["tmdb_id"]
        elif "_id" in res:
            res["id"] = abs(hash(str(res["_id"]))) % 2147483647 + 1
        else:
            res["id"] = 1

    return res
