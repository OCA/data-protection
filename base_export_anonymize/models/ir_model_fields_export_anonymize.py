# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrModelFieldsExportAnonymize(models.Model):

    _name = "ir.model.fields.export.anonymize"
    _description = "Ir Model Fields Export Anonymize"

    field_id = fields.Many2one(
        comodel_name="ir.model.fields", string="Field", required=True, index=True
    )
