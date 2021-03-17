# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrModelFields(models.Model):

    _inherit = "ir.model.fields"

    anonymize_in_export = fields.Boolean(
        string="Anonymize In Export",
        compute="_compute_anonymize_in_export",
        inverse="_inverse_anonymize_in_export",
    )

    @api.multi
    def _compute_anonymize_in_export(self):
        fields_anonymize_model = self.env["ir.model.fields.export.anonymize"]
        for rec in self:
            rec.anonymize_in_export = False
            if fields_anonymize_model.search([("field_id", "=", rec.id)]):
                rec.anonymize_in_export = True
