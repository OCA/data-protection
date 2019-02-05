# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _

FIELDS_GDPR = [
    'image',
    'name',
    'street',
    'street2',
    'zip',
    'city',
    'website',
    'function',
    'phone',
    'mobile',
    'fax',
    'email',
    'title',
    'child_ids',
]


class ResPartnerGdpr(models.TransientModel):
    _name = 'res.partner.gdpr'

    def _default_fields(self):
        res_partner = self.env['ir.model'].search([
            ('model', '=', 'res.partner')])
        return [(6, 0, self.env['ir.model.fields'].search([
            ('model_id', '=', res_partner.id),
            ('name', 'in', FIELDS_GDPR)]).ids)]

    partner_ids = fields.Many2many('res.partner')
    fields = fields.Many2many(
        'ir.model.fields',
        default=_default_fields,
        domain=[('model_id.model', '=', 'res.partner')],
        help='Fields to delete data from.',
    )

    @api.multi
    def _get_remove_text(self):
        return _('*** GDPR removed ***')

    @api.multi
    def action_gdpr_res_partner_cleanup(self):
        self._pre_gdpr_cleanup()
        self._gdpr_cleanup()
        self._post_gdpr_cleanup()

    @api.multi
    def _pre_gdpr_cleanup(self):
        if 'child_ids' in self.fields.mapped('name'):
            childs = self.partner_ids.mapped('child_ids')
            all_partners = self.partner_ids | childs
            self.partner_ids = all_partners.ids
        pass

    @api.model
    def _do_gdpr_cleanup(self, fields, records):
        vals = {}
        for field in fields:
            if field.ttype in ['many2one', 'binary']:
                vals.update({field.name: False})
            elif field.ttype in ['many2many']:
                vals.update({field.name: [(5, _, _)]})
            # To improve...
            elif field.ttype in ['one2many']:
                continue
            else:
                vals.update({field.name: self._get_remove_text()})
        records.write(vals)

    @api.multi
    def _gdpr_cleanup(self):
        self.ensure_one()
        self._do_gdpr_cleanup(self.fields, self.partner_ids)

    @api.multi
    def _post_gdpr_cleanup(self):
        self.partner_ids.write({'active': False})
