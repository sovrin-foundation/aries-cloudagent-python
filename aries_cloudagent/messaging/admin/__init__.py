"""More condensed method of generating a message and its schema."""

import sys
from ..agent_message import AgentMessage, AgentMessageSchema

# pylint: disable=invalid-name


def generic_init(instance, **kwargs):
    """Initialize from kwargs into slots."""
    for slot in instance.__slots__:
        setattr(instance, slot, kwargs.get(slot))
        if slot in kwargs:
            del kwargs[slot]
    super(type(instance), instance).__init__(**kwargs)


def generate_model_schema(model_name, handler_class, message_type, schema_dict):
    """
    Generate a Message model class and schema class programmatically.

    The following would result in a class named XYZ inheriting from AgentMessage
    and XYZSchema inheriting from AgentMessageSchema.

    XYZ, XYZSchema = generate_model_schema(
        'XYZ',
        'aries_cludagent.admin.handlers.XYZHandler',
        '{}/xyz'.format(PROTOCOL),
        {}
    )

    The attributes of XYZ are determined by schema_dict's keys. The actual
    schema of XYZSchema is defined by the field-value combinations of
    schema_dict, similar to marshmallow's Schema.from_dict() (can't actually
    use that here as the model_class must be set in the Meta inner-class of
    AgentMessageSchema's).
    """
    Model = type(
        model_name,
        (AgentMessage,),
        {
            'Meta': type(
                'Meta', (), {
                    '__qualname__': model_name + '.Meta',
                    'handler_class': handler_class,
                    'message_type': message_type,
                    'schema_class': model_name + 'Schema',
                }
            ),
            '__init__': generic_init,
            '__slots__': list(schema_dict.keys())
        }
    )
    Model.__module__ = sys._getframe(1).f_globals['__name__']
    Schema = type(
        model_name + 'Schema',
        (AgentMessageSchema,),
        {
            'Meta': type(
                'Meta', (), {
                    '__qualname__': model_name + 'Schema.Meta',
                    'model_class': Model,
                }
            ),
            **schema_dict
        }
    )
    Schema.__module__ = sys._getframe(1).f_globals['__name__']
    return Model, Schema
