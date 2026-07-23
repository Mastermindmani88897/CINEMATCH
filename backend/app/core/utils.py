from typing import Any, Dict, List
from bson import ObjectId


def serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively converts MongoDB document `_id` and BSON ObjectIds to string `id`
    so Pydantic schemas and frontend receive standard JSON objects.
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
            if "id" not in doc:
                res["id"] = str(v) if not isinstance(v, int) else v
        elif isinstance(v, ObjectId):
            res[k] = str(v)
        elif isinstance(v, dict):
            res[k] = serialize_doc(v)
        elif isinstance(v, list):
            res[k] = [serialize_doc(item) for item in v]
        else:
            res[k] = v
    return res
