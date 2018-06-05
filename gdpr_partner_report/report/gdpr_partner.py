# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import api, fields, models


class ReportPartner(models.AbstractModel):
    _name = 'report.gdpr.report_partner'

    @api.multi
    def render_html(self, data):
        docs = self.env['gdpr.partner.report'].browse(
            self.env.context.get('active_ids', []))
        partner = data['form'].get('partner_id', False)
        partner = self.env['res.partner'].browse(partner[0])
        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'gdpr.partner.report',
            'data': data['form'],
            'docs': docs,
            'date': fields.date.today(),
            'tables': data['tables'],
            'partner': partner,
        }
        return self.env['report'].render(
            'gdpr_partner_report.report_partner', values=docargs)
