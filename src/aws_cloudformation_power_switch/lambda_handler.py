import os
import jsonschema
import logging
from .master import power_switch

schema = {
    "type": "object",
    "required": [ "stack_name_prefix"],
    "properties": {
        "stack_name_prefix": {
            "type": "string"
        },
        "profile": {
            "type": "string"
        },
        "region": {
            "type": "string"
        },
        "verbose": {
            "type": "boolean",
            "default": True
        },
        "dry_run": {
            "type": "boolean",
            "default": False
        },
        "state": {
            "type": "string",
            "enum": ["on", "off"]
        }
    }
}

def is_valid_request(request) -> bool:
    try:
        jsonschema.validate(request, schema)
        return True
    except jsonschema.ValidationError as e:
        logging.error('invalid request received: %s' % str(e.context))
        return False


def handler(request, context):
    logging.getLogger().setLevel(os.getenv("LOG_LEVEL", "INFO"))
    if is_valid_request(request):
        state = request["state"]
        request.pop("state")
        switch = power_switch(**request)
        if state == "off":
            switch.off()
        else:
            switch.on()
