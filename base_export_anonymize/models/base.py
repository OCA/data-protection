# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class Base(models.AbstractModel):

    _inherit = "base"

    @api.model
    def _export_anonymize(self, rows, index):
        anonymize_key = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("model.fields.export.anonymize.key", "***********")
        )
        for row in rows:
            row[index] = anonymize_key

    @api.multi
    def _export_rows(self, *args, **kwargs):
        rows = super()._export_rows(*args, **kwargs)
        if self.env.user.has_group(
            "base_export_anonymize.group_anonymize_data_in_export"
        ):
            fields = args[0]
            field_model = self.env["ir.model.fields"]
            for index, path in enumerate(fields):
                if len(path) == 1:
                    field_name = path[0]
                    if self._fields.get(field_name):
                        model_name = self._fields.get(field_name).model_name
                        field = field_model.search(
                            [
                                ("model", "=", model_name),
                                ("name", "=", field_name),
                            ]
                        )
                        if field.anonymize_in_export:
                            self._export_anonymize(rows, index)
        return rows
