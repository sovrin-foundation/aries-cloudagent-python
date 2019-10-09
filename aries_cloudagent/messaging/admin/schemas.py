"""Define messages for schemas admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from asyncio import shield

from marshmallow import fields

from . import generate_model_schema, admin_only
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ...ledger.base import BaseLedger

PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/1.0'

SEND_SCHEMA = '{}/send-schema'.format(PROTOCOL)
SCHEMA_ID = '{}/schema-id'.format(PROTOCOL)
SCHEMA_GET = '{}/schema-get'.format(PROTOCOL)
SCHEMA = '{}/schema'.format(PROTOCOL)

MESSAGE_TYPES = {
    SEND_SCHEMA:
        'aries_cloudagent.messaging.admin.schemas'
        '.SendSchema',
    SCHEMA_ID:
        'aries_cloudagent.messaging.admin.schemas'
        '.SchemaID',
    SCHEMA_GET:
        'aries_cloudagent.messaging.admin.schemas'
        '.SchemaGet',
    SCHEMA:
        'aries_cloudagent.messaging.admin.schemas'
        '.Schema'
}

SendSchema, SendSchemaSchema = generate_model_schema(
    name='SendSchema',
    handler='aries_cloudagent.messaging.admin.schemas.SendSchemaHandler',
    msg_type=SEND_SCHEMA,
    schema={
        'schema_name': fields.Str(required=True),
        'schema_version': fields.Str(required=True),
        'attributes': fields.List(fields.Str(), required=True)
    }
)
SchemaID, SchemaIDSchema = generate_model_schema(
    name='SchemaID',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=SCHEMA_ID,
    schema={
        'schema_id': fields.Str()
    }
)


class SendSchemaHandler(BaseHandler):
    """Handler for received send schema request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send schema request."""
        ledger: BaseLedger = await context.inject(BaseLedger)
        async with ledger:
            schema_id = await shield(
                ledger.send_schema(
                    context.message.schema_name,
                    context.message.schema_version,
                    context.message.attributes
                )
            )
        result = SchemaID(schema_id=schema_id)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


SchemaGet, SchemaGetSchema = generate_model_schema(
    name='SchemaGet',
    handler='aries_cloudagent.messaging.admin.schemas.SchemaGetHandler',
    msg_type=SCHEMA_GET,
    schema={
        'schema_id': fields.Str(required=True)
    }
)
Schema, SchemaSchema = generate_model_schema(
    name='Schema',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=SCHEMA,
    schema={
        'schema': fields.Dict()
    }
)


class SchemaGetHandler(BaseHandler):
    """Handler for received schema get request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received schema get request."""

        ledger: BaseLedger = await context.inject(BaseLedger)
        async with ledger:
            schema = await ledger.get_schema(context.message.schema_id)

        schema_msg = Schema(schema=schema)
        schema_msg.assign_thread_from(context.message)
        await responder.send_reply(schema_msg)
