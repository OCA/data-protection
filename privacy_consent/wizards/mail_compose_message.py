# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    @api.multi
    def send_mail(self, auto_commit=False):
        """Update consent state if needed."""
        if (self.env.context.get('active_model') == 'privacy.consent' and
                self.env.context.get('active_ids') and
                self.env.context.get('mark_consent_sent')):
            consents = self.env['privacy.consent'].browse(
                self.env.context['active_ids'],
                self._prefetch,
            )
            consents.filtered(lambda one: one.state == "draft") \
                .with_context(tracking_disable=True) \
                .write({"state": "sent"})
        return super(MailComposeMessage, self).send_mail(
            auto_commit=auto_commit)
