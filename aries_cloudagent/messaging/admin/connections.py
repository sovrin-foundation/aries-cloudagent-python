"""Define messages for connections admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import fields, validate

from . import generate_model_schema, admin_only
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ..connections.models.connection_record import (
    ConnectionRecord, ConnectionRecordSchema
)


PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-connections/1.0'

# Message Types
CONNECTION_GET_LIST = '{}/connection-get-list'.format(PROTOCOL)
CONNECTION_LIST = '{}/connection-list'.format(PROTOCOL)
CONNECTION_GET = '{}/connection-get'.format(PROTOCOL)
CONNECTION = '{}/connection'.format(PROTOCOL)
CREATE_INVITATION = '{}/create-invitiation'.format(PROTOCOL)
INVITATION = '{}/invitation'.format(PROTOCOL)
RECEIVE_INVITATION = '{}/receive-invitation'.format(PROTOCOL)
ACCEPT_INVITATION = '{}/accept-invitation'.format(PROTOCOL)
ACCEPT_REQUEST = '{}/accept-request'.format(PROTOCOL)
ESTABLISH_INBOUND = '{}/establish-inbound'.format(PROTOCOL)
DELETE_CONNECTION = '{}/delete-connection-request'.format(PROTOCOL)

# Message Type string to Message Class map
MESSAGE_TYPES = {
    CONNECTION_GET_LIST:
        'aries_cloudagent.messaging.admin.connections'
        '.ConnectionGetList',
    CONNECTION_LIST:
        'aries_cloudagent.messaging.admin.connections'
        '.ConnectionList',
    CONNECTION_GET:
        'aries_cloudagent.messaging.admin.connections'
        '.ConnectionGet',
    CONNECTION:
        'aries_cloudagent.messaging.admin.connections'
        '.Connnection',
    CREATE_INVITATION:
        'aries_cloudagent.messaging.admin.connections'
        '.CreateInvitation',
    INVITATION:
        'aries_cloudagent.messaging.admin.connections'
        '.Invitation',
    RECEIVE_INVITATION:
        'aries_cloudagent.messaging.admin.connections'
        '.ReceiveInvitation',
    ACCEPT_INVITATION:
        'aries_cloudagent.messaging.admin.connections'
        '.AcceptInvitation',
    ACCEPT_REQUEST:
        'aries_cloudagent.messaging.admin.connections'
        '.AcceptRequest',
    ESTABLISH_INBOUND:
        'aries_cloudagent.messaging.admin.connections'
        '.EstablishInbound',
    DELETE_CONNECTION:
        'aries_cloudagent.messaging.admin.connections'
        '.DeleteConnection',
}


ConnectionGetList, ConnectionGetListSchema = generate_model_schema(
    'ConnectionGetList',
    'aries_cloudagent.messaging.admin.connections.ConnectionGetListHandler',
    CONNECTION_GET_LIST,
    {
        'initiator': fields.Str(
            validate=validate.OneOf(['self', 'external']),
            required=False,
        ),
        'invitation_key': fields.Str(required=False),
        'my_did': fields.Str(required=False),
        'state': fields.Str(
            validate=validate.OneOf([
                'init',
                'invitation',
                'request',
                'response',
                'active',
                'error',
                'inactive'
            ]),
            required=False
        ),
        'their_did': fields.Str(required=False),
        'their_role': fields.Str(required=False)
    }
)
ConnectionList, ConnectionListSchema = generate_model_schema(
    'ConnectionList',
    'aries_cloudagent.messaging.admin.PassHandler',
    CONNECTION_LIST,
    {
        'results': fields.List(
            fields.Nested(ConnectionRecordSchema),
            required=True
        )
    }
)


class ConnectionGetListHandler(BaseHandler):
    """Handler for get connection list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get connection list request."""

        def connection_sort_key(conn):
            """Get the sorting key for a particular connection."""
            if conn["state"] == ConnectionRecord.STATE_INACTIVE:
                pfx = "2"
            elif conn["state"] == ConnectionRecord.STATE_INVITATION:
                pfx = "1"
            else:
                pfx = "0"
            return pfx + conn["created_at"]

        tag_filter = dict(
            filter(lambda item: item[1] is not None, {
                'initiator': context.message.initiator,
                'invitation_key': context.message.invitation_key,
                'my_did': context.message.my_did,
                'state': context.message.state,
                'their_did': context.message.their_did,
                'their_role': context.message.their_role
            }.items())
        )
        records = await ConnectionRecord.query(context, tag_filter)
        results = []
        for record in records:
            row = record.serialize()
            row["activity"] = await record.fetch_activity(context)
            results.append(row)
        results.sort(key=connection_sort_key)
        connection_list = ConnectionList(results=results)
        connection_list.assign_thread_from(context.message)
        await responder.send_reply(connection_list)


ConnectionGet, ConnectionGetSchema = generate_model_schema(
    'ConnectionGet',
    'aries_cloudagent.messaging.admin.connections.ConnectionGetHandler',
    CONNECTION_GET,
    {
        'connection_id': fields.Str(required=True)
    }
)

Connection, ConnectionSchema = generate_model_schema(
    'Connection',
    'aries_cloudagent.messaging.admin.PassHandler',
    CONNECTION,
    {
        'connection': fields.Nested(ConnectionRecordSchema, required=True),
    }
)

CreateInvitation, CreateInvitationSchema = generate_model_schema(
    'CreateInvitation',
    'aries_cloudagent.messaging.admin.connections.CreateInvitationHandler',
    CREATE_INVITATION,
    {
        'accept': fields.Boolean(missing=False),
        'public': fields.Boolean(missing=False),
        'multi_use': fields.Boolean(missing=False)
    }
)

Invitation, InvitationSchema = generate_model_schema(
    'Invitation',
    'aries_cloudagent.messaging.admin.PassHandler',
    INVITATION,
    {
        'connection_id': fields.Str(required=True),
        'invitation': fields.Str(required=True),
        'invitation_url': fields.Str(required=True)
    }
)

ReceiveInvitation, ReceiveInvitationSchema = generate_model_schema(
    'ReceiveInvitation',
    'aries_cloudagent.messaging.admin.connections.ReceiveInvitationHandler',
    RECEIVE_INVITATION,
    {
        'invitation': fields.Str(required=True),
        'accept': fields.Boolean(missing=False)
    }
)

AcceptInvitation, AcceptInvitationSchema = generate_model_schema(
    'AcceptInvitation',
    'aries_cloudagent.messaging.admin.connections.AcceptInvitationHandler',
    ACCEPT_INVITATION,
    {
        'connection_id': fields.Str(required=True),
        'my_endpoint': fields.Str(required=False),
        'my_label': fields.Str(required=False),
    }
)

AcceptRequest, AcceptRequestSchema = generate_model_schema(
    'AcceptRequest',
    'aries_cloudagent.messaging.admin.connections.AcceptRequestHandler',
    ACCEPT_REQUEST,
    {
        'connection_id': fields.Str(required=True),
        'my_endpoint': fields.Str(required=False),
    }
)

EstablishInbound, EstablishInboundSchema = generate_model_schema(
    'EstablishInbound',
    'aries_cloudagent.messaging.admin.connections.EstablishInboundHandler',
    ESTABLISH_INBOUND,
    {
        'connection_id': fields.Str(required=True),
        'ref_id': fields.Str(required=True),
    }
)

DeleteConnection, DeleteConnectionSchema = generate_model_schema(
    'DeleteConnection',
    'aries_cloudagent.messaging.admin.connections.DeleteConnectionHandler',
    DELETE_CONNECTION,
    {
        'connection_id': fields.Str(required=True),
    }
)
