# -*- coding: utf-8 -*-
# Copyright 2019 Akretion <https://akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, models

CRM_GDPR_FIELDS = [
    'name',
    'email_from',
    'email_cc',
    'description',
    'contact_name',
    'partner_name',
    'referred',
    'phone',
    'street',
    'street2',
    'zip',
    'city',
    'state_id',
    'phone',
    'fax',
    'mobile',
    'function',
    'title',
    'message_ids',
]


class ResPartnerGdpr(models.TransientModel):
    _inherit = 'res.partner.gdpr'

    @api.multi
    def _post_gdpr_cleanup(self):
        super(ResPartnerGdpr, self)._post_gdpr_cleanup()
        leads = self.env['crm.lead'].with_context(active_test=False).search(
            [('partner_id', 'in', self.partner_ids.ids)])
        if leads:
            lead_model = self.env['ir.model'].search([
                ('model', '=', 'crm.lead')])
            fields = self.env['ir.model.fields'].search([
                ('model_id', '=', lead_model.id),
                ('name', 'in', CRM_GDPR_FIELDS)])
            self._do_gdpr_cleanup(fields, leads)
            leads.write({'active': False})
