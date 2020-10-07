# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _postprocess_sent_message(self, success_pids, failure_reason=False,
                                  failure_type=None):
        """Write consent status after sending message."""
        # Know if mail was successfully sent to a privacy consent
        if (
            self.mail_message_id.model == "privacy.consent"
            and self.state == "sent"
            and success_pids
            and not failure_reason
            and not failure_type
        ):
            # Get related consent
            consent = self.env["privacy.consent"].browse(
                self.mail_message_id.res_id,
                self._prefetch,
            )
            # Set as sent if needed
            if (
                consent.state == "draft"
                and consent.partner_id.id in {par.id for par in success_pids}
            ):
                consent.write({
                    "state": "sent",
                })
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
        result = super(MailMail, self)._send_prepare_body()
        # Avoid polluting other model mails
        if self.model != "privacy.consent":
            return result
        # Tokenize consent links
        consent = self.env["privacy.consent"] \
            .browse(self.mail_message_id.res_id) \
            .with_prefetch(self._prefetch)
        result = result.replace(
            "/privacy/consent/accept/",
            consent._url(True),
        )
        result = result.replace(
            "/privacy/consent/reject/",
            consent._url(False),
        )
        return result
