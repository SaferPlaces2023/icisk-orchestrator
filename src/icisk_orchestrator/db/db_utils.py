from typing import Any

def cast_to_schema(schema: Any, record: dict | list[dict] | None) -> Any:
    """
    Cast a dictionary to a schema object.
    
    Args:
        schema (Any): The schema to cast to.
        record (dict): The dictionary to cast.
        
    Returns:
        Any: The casted object.
    """
    
    if record is None:
        return None
    
    if isinstance(record, list):
        return [schema.from_dict(r) for r in record]
    else:
        return schema.from_dict(record)