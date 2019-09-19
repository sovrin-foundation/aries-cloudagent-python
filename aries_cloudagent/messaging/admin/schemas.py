"""Define messages for schemas admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from asyncio import shield

from marshmallow import fields

from . import generate_model_schema
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ...ledger.base import BaseLedger

PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/1.0'

SEND_SCHEMA = '{}/send-schema'.format(PROTOCOL)
SCHEMA_ID = '{}/schema-id'.format(PROTOCOL)
SCHEMA_GET = '{}/schema-get'.format(PROTOCOL)
SCHEMA = '{}/schema'.format(PROTOCOL)

MESSAGE_TYPES = {
    SEND_SCHEMA:
        'aries_cloudagent.messages.admin.schemas'
        '.SendSchema',
    SCHEMA_ID:
        'aries_cloudagent.messages.admin.schemas'
        '.SchemaID',
    SCHEMA_GET:
        'aries_cloudagent.messages.admin.schemas'
        '.SchemaGet',
    SCHEMA:
        'aries_cloudagent.messages.admin.schemas'
        '.Schema'
}

SendSchema, SendSchemaSchema = generate_model_schema(
    'SendSchema',
    'aries_cloudagent.messaging.admin.schemas.SendSchemaHandler',
    SEND_SCHEMA,
    {
        'schema_name': fields.Str(required=True),
        'schema_version': fields.Str(required=True),
        'attributes': fields.List(fields.Str(), required=True)
    }
)
SchemaID, SchemaIDSchema = generate_model_schema(
    'SchemaID',
    'aries_cloudagent.messaging.admin.PassHandler',
    SCHEMA_ID,
    {
        'schema_id': fields.Str()
    }
)


class SendSchemaHandler(BaseHandler):
    """Handler for received send schema request."""

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
    'SchemaGet',
    'aries_cloudagent.messaging.admin.schemas.SchemaGetHandler',
    SCHEMA_GET,
    {
        'schema_id': fields.Str(required=True)
    }
)
Schema, SchemaSchema = generate_model_schema(
    'Schema',
    'aries_cloudagent.messaging.admin.PassHandler',
    SCHEMA,
    {
        'schema': fields.Dict()
    }
)


class SchemaGetHandler(BaseHandler):
    """Handler for received schema get request."""

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received schema get request."""

        ledger: BaseLedger = await context.inject(BaseLedger)
        async with ledger:
            schema = await ledger.get_schema(context.message.schema_id)

        schema_msg = Schema(schema=schema)
        schema_msg.assign_thread_from(context.message)
        await responder.send_reply(schema_msg)
