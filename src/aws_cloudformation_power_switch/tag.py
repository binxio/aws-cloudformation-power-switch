
def value(instance:dict, key:str) -> str:
    """
    gets the first value of the AWS object `instance` tag, or "" if not found
    """
    tags = instance.get("Tags", instance.get("TagList", []))
    return next(iter(map(lambda c: c["Value"], filter(lambda t: t["Key"] == key, tags))), "")

def stack_name(instance:dict) -> str:
    return value(instance, "aws:cloudformation:stack-name")

def logical_id(instance:dict) -> str:
    return value(instance, "aws:cloudformation:logical-id")