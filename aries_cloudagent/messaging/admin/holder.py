"""Define messages for credential holder admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import fields

from . import generate_model_schema, admin_only
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

PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/1.0'

SEND_PROPOSAL = '{}/send-proposal'.format(PROTOCOL)
CRED_EXCHANGE = '{}/credential-exchange'.format(PROTOCOL)
CREDENTIALS_GET_LIST = '{}/credentials-get-list'.format(PROTOCOL)
CREDENTIALS_LIST = '{}/credentials-list'.format(PROTOCOL)

MESSAGE_TYPES = {
    SEND_PROPOSAL:
        'aries_cloudagent.messaging.admin.holder.SendProposal',
    CREDENTIALS_GET_LIST:
        'aries_cloudagent.messaging.admin.holder.CredGetList',
    CREDENTIALS_LIST:
        'aries_cloudagent.messaging.admin.holder.CredList',
}

SendProposal, SendProposalSchema = generate_model_schema(
    name='SendProposal',
    handler='aries_cloudagent.messaging.admin.holder.SendProposalHandler',
    msg_type=SEND_PROPOSAL,
    schema=V10CredentialProposalRequestSchema
)

CredExchange, CredExchangeSchema = generate_model_schema(
    name='CredExchange',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=CRED_EXCHANGE,
    schema=V10CredentialExchangeSchema
)


class SendProposalHandler(BaseHandler):
    """Handler for received send proposal request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send proposal request."""
        connection_id = str(context.message.connection_id)
        credential_definition_id = context.message.credential_definition_id
        comment = context.message.comment
        credential_preview = context.message.credential_proposal

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

        credential_exchange_record = await credential_manager.create_proposal(
            connection_id,
            comment=comment,
            credential_preview=credential_preview,
            credential_definition_id=credential_definition_id
        )

        await responder.send(
            CredentialProposal.deserialize(
                credential_exchange_record.credential_proposal_dict
            ),
            connection_id=connection_id
        )
        cred_exchange = CredExchange(**credential_exchange_record.serialize())
        cred_exchange.assign_thread_from(context.message)
        await responder.send_reply(cred_exchange)


CredGetList, CredGetListSchema = generate_model_schema(
    name='CredGetList',
    handler='aries_cloudagent.messaging.admin.holder.CredGetListHandler',
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
                # 'state': V10CredentialExchange.STATE_CREDENTIAL_RECEIVED,
                'connection_id': context.message.connection_id,
                'credential_definition_id': context.message.credential_definition_id,
                'schema_id': context.message.schema_id
            }.items())
        )
        records = await V10CredentialExchange.query(context, tag_filter)
        cred_list = CredList(results=records)
        await responder.send_reply(cred_list)
