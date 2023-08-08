from jsonschema import validate, ValidationError

# Command
command_schema = {
    "type": "object",
    "properties": {
        "uuid": {"type": "string"},
        "interface": {
            "type": "string",
            "enum" : ["topic", "service", "action_send_goal", "action_cancel_goal"]
          },
        "name": {"type": "string", "minLength": 1},
        "type": {
            "type": "string",
            "pattern": r".+/.+/.+"
        },
        "payload": {
            "type": "object"
        }
    },
    "required": ["uuid", "interface", "name", "type", "payload" ]
}


# Container update
container_update_schema = {
    "type": "object",
    "properties": {
        "compose": {
            "type": ["object", "null"]
        }
    },
    "required": ["compose" ]
}