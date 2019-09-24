"""Define messages for static connections management admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import fields

from ...wallet.base import BaseWallet

from . import generate_model_schema, admin_only
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ..connections.manager import ConnectionManager
from ..connections.models.connection_record import ConnectionRecord
from ..connections.models.diddoc import (
    DIDDoc, PublicKey, PublicKeyType, Service
)


PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-static-connections/1.0'

# Message Types
CREATE_STATIC_CONNECTION = '{}/create-static-connection'.format(PROTOCOL)
STATIC_CONNECTION_INFO = '{}/static-connection-info'.format(PROTOCOL)

# Message Type to Message Class Map
MESSAGE_TYPES = {
    CREATE_STATIC_CONNECTION:
        'aries_cloudagent.messaging.admin.static_connections'
        '.CreateStaticConnection',
    STATIC_CONNECTION_INFO:
        'aries_cloudagent.messaging.admin.static_connections'
        '.StaticConnectionInfo',
}

# Models and Schemas
CreateStaticConnection, CreateStaticConnectionSchema = generate_model_schema(
    name='CreateStaticConnection',
    handler='aries_cloudagent.messaging.admin.static_connections'
            '.CreateStaticConnectionHandler',
    msg_type=CREATE_STATIC_CONNECTION,
    schema={
        'label': fields.Str(required=True),
        'role': fields.Str(required=False),
        'static_did': fields.Str(required=True),
        'static_key': fields.Str(required=True),
        'static_endpoint': fields.Str(missing='')
    }
)
StaticConnectionInfo, StaticConnectionInfoSchema = generate_model_schema(
    name='StaticConnectionInfo',
    handler='aries_cloudagent.messaging.admin.static_connections'
            '.StaticConnectionInfoHandler',
    msg_type=STATIC_CONNECTION_INFO,
    schema={
        'did': fields.Str(required=True),
        'key': fields.Str(required=True),
        'endpoint': fields.Str(required=True)
    }
)


class CreateStaticConnectionHandler(BaseHandler):
    """Handler for static connection creation requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle static connection creation request."""

        connection_mgr = ConnectionManager(context)
        wallet: BaseWallet = await context.inject(BaseWallet)

        # Make our info for the connection
        my_info = await wallet.create_local_did()

        # Create connection record
        connection = ConnectionRecord(
            initiator=ConnectionRecord.INITIATOR_SELF,
            my_did=my_info.did,
            their_did=context.message.static_did,
            their_label=context.message.label,
            their_role=context.message.role if context.message.role else None,
            state=ConnectionRecord.STATE_STATIC,
        )

        # Construct their did doc from the basic components in message
        diddoc = DIDDoc(context.message.static_did)
        public_key = PublicKey(
            did=context.message.static_did,
            ident="1",
            value=context.message.static_key,
            pk_type=PublicKeyType.ED25519_SIG_2018,
            controller=context.message.static_did
        )
        service = Service(
            did=context.message.static_did,
            ident="indy",
            typ="IndyAgent",
            recip_keys=[public_key],
            routing_keys=[],
            endpoint=context.message.static_endpoint
        )
        diddoc.set(public_key)
        diddoc.set(service)

        # Save
        await connection_mgr.store_did_document(diddoc)
        await connection.save(
            context,
            reason='Created new static connection'
        )

        # Prepare response
        info = StaticConnectionInfo(
            did=my_info.did,
            key=my_info.verkey,
            endpoint=context.settings.get("default_endpoint")
        )
        info.assign_thread_from(context.message)
        await responder.send_reply(info)
        return
