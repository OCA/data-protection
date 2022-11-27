# Copyright 2018 Tecnativa - Jairo Llopis
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _postprocess_sent_message(
        self, success_pids, failure_reason=False, failure_type=None
    ):
        """Write consent status after sending message."""
        # Know if mail was successfully sent to a privacy consent
        res_ids = []
        for mail in self:
            if (
                mail.mail_message_id.model == "privacy.consent"
                and mail.state == "sent"
                and success_pids
                and not failure_reason
                and not failure_type
            ):
                res_ids.append(mail.mail_message_id.res_id)
        if res_ids:
            consents = self.env["privacy.consent"].search(
                [
                    ("id", "in", res_ids),
                    ("state", "=", "draft"),
                    ("partner_id", "in", [par.id for par in success_pids]),
                ]
            )
            consents.write({"state": "sent"})
        return super()._postprocess_sent_message(
            success_pids=success_pids,
            failure_reason=failure_reason,
            failure_type=failure_type,
        )

    def _send_prepare_body(self):
        """Replace privacy consent magic links.

        This replacement is done here instead of directly writing it into
        the ``mail.template`` to avoid writing the tokeinzed URL
        in the mail thread for the ``privacy.consent`` record,
        which would enable any reader of such thread to impersonate the
        subject and choose in its behalf.
        """
        result = super()._send_prepare_body()
        # Avoid polluting other model mails
        if self.model != "privacy.consent":
            return result
        # Tokenize consent links
        consent = self.env["privacy.consent"].browse(self.mail_message_id.res_id)
        result = result.replace(
            "/privacy/consent/accept/",
            consent._url(True),
        )
        result = result.replace(
            "/privacy/consent/reject/",
            consent._url(False),
        )
        return result
