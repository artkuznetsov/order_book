from jsonschema import validate
from jsonschema.exceptions import ValidationError


def is_market_data_schema_valid(market_data):
    market_data_schema = {
        "definitions": {
            "order": {
                "$id": "#order",
                "type": "array",
                "properties": {
                    "price": {"type": "number"},
                    "quantity": {"type": "number"}
                }
            }

        },
        "type": "object",
        "properties": {
            "asks": {"type": "array", "$ref": "#/definitions/order"},
            "bids": {"type": "array", "$ref": "#/definitions/order"}
        },
        'required': ['asks', 'bids']

    }
    try:
        validate(instance=market_data, schema=market_data_schema)
        return True
    except ValidationError as e:
        return False, e
