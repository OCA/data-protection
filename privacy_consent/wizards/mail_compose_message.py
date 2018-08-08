# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    @api.multi
    def send_mail(self, auto_commit=False):
        """Force auto commit when sending consent emails."""
        if self.env.context.get('mark_consent_sent'):
            auto_commit = True
        return super(MailComposeMessage, self).send_mail(auto_commit)
