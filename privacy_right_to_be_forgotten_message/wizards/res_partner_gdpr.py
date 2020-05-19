# -*- coding: utf-8 -*-
# Copyright 2019 Akretion <https://akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, models
from openerp.addons.privacy_right_to_be_forgotten.wizards import (
    res_partner_gdpr
)

FIELDS_GDPR = [
    'message_ids'
]
res_partner_gdpr.FIELDS_GDPR += FIELDS_GDPR


class ResPartnerGdpr(models.TransientModel):
    _inherit = 'res.partner.gdpr'

    @api.model
    def _do_gdpr_cleanup(self, fields, records):
        res = super(ResPartnerGdpr, self)._do_gdpr_cleanup(fields, records)
        message_field = fields.filtered(
            lambda f: f.name == 'message_ids' and
            f.relation == 'mail.message')
        if message_field:
            messages = records.mapped('message_ids')
            messages.unlink()
        return res
