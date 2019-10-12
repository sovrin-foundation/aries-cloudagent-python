"""Define messages for credential issuer admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
import asyncio

from marshmallow import fields

from . import generate_model_schema, admin_only
from .holder import CredExchange
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ..issue_credential.v1_0.routes import (
    V10CredentialExchangeListResultSchema,
    V10CredentialProposalRequestSchema
)
from ..issue_credential.v1_0.models.credential_exchange import (
    V10CredentialExchange,
    V10CredentialExchangeSchema
)
from ..issue_credential.v1_0.messages.credential_proposal import (
    CredentialProposal
)
from ..issue_credential.v1_0.manager import CredentialManager
from ..connections.models.connection_record import ConnectionRecord
from ...storage.error import StorageNotFoundError
from ..problem_report.message import ProblemReport

PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-issuer/1.0'

SEND = '{}/send'.format(PROTOCOL)
CREDENTIALS_GET_LIST = '{}/credentials-get-list'.format(PROTOCOL)
CREDENTIALS_LIST = '{}/credentials-list'.format(PROTOCOL)

MESSAGE_TYPES = {
    SEND:
        'aries_cloudagent.messaging.admin.issuer.Send',
    CREDENTIALS_GET_LIST:
        'aries_cloudagent.messaging.admin.issuer.CredGetList',
    CREDENTIALS_LIST:
        'aries_cloudagent.messaging.admin.issuer.CredList',
}

Send, SendSchema = generate_model_schema(
    name='Send',
    handler='aries_cloudagent.messaging.admin.issuer.SendHandler',
    msg_type=SEND,
    schema=V10CredentialProposalRequestSchema
)


class SendHandler(BaseHandler):
    """Handler for received send request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send request."""
        connection_id = str(context.message.connection_id)
        credential_definition_id = context.message.credential_definition_id
        comment = context.message.comment
        credential_proposal = CredentialProposal(
            comment=comment,
            credential_proposal=context.message.credential_proposal,
            cred_def_id=credential_definition_id,
        )

        credential_manager = CredentialManager(context)

        try:
            connection_record = await ConnectionRecord.retrieve_by_id(
                context,
                connection_id
            )
        except StorageNotFoundError:
            report = ProblemReport(
                explain_ltxt='Connection not found.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        if not connection_record.is_ready:
            report = ProblemReport(
                explain_ltxt='Connection invalid.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        credential_exchange_record = await credential_manager.prepare_send(
            credential_definition_id,
            connection_id,
            credential_proposal=credential_proposal
        )
        asyncio.ensure_future(
            credential_manager.perform_send(
                credential_exchange_record,
                responder.send
            )
        )
        cred_exchange = CredExchange(**credential_exchange_record.serialize())
        cred_exchange.assign_thread_from(context.message)
        await responder.send_reply(cred_exchange)


CredGetList, CredGetListSchema = generate_model_schema(
    name='CredGetList',
    handler='aries_cloudagent.messaging.admin.issuer.CredGetListHandler',
    msg_type=CREDENTIALS_GET_LIST,
    schema={
        'connection_id': fields.Str(required=False),
        'credential_definition_id': fields.Str(required=False),
        'schema_id': fields.Str(required=False)
    }
)

CredList, CredListSchema = generate_model_schema(
    name='CredList',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=CREDENTIALS_LIST,
    schema=V10CredentialExchangeListResultSchema
)


class CredGetListHandler(BaseHandler):
    """Handler for received get cred list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get cred list request."""

        tag_filter = dict(
            filter(lambda item: item[1] is not None, {
                # 'state': V10CredentialExchange.STATE_ISSUED,
                'role': V10CredentialExchange.ROLE_ISSUER,
                'connection_id': context.message.connection_id,
                'credential_definition_id': context.message.credential_definition_id,
                'schema_id': context.message.schema_id
            }.items())
        )
        records = await V10CredentialExchange.query(context, tag_filter)
        cred_list = CredList(results=records)
        await responder.send_reply(cred_list)
