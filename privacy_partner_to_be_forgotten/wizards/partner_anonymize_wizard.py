# Copyright (C) 2025 Cetmix OÜ
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class PartnerAnonymizeWizard(models.TransientModel):
    _name = "partner.anonymize.wizard"
    _description = "Partner Anonymization Wizard"

    partner_ids = fields.Many2many(
        "res.partner",
        required=True,
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self._context.get("active_ids")
        if "partner_ids" in fields_list and active_ids:
            domain = [
                ("id", "child_of", active_ids),
                "|",
                ("email", "=", False),
                ("email", "not like", "%@anonymized.oca"),
            ]
            all_partners = self.env["res.partner"].search(domain)
            res["partner_ids"] = [(6, 0, all_partners.ids)]
        return res

    def _validate_partners_for_anonymization(self):
        # Check access rights
        if not self.env.user.has_group(
            "privacy_partner_to_be_forgotten.group_partner_anonymize"
        ):
            raise AccessError(_("You don't have permission to anonymize partners."))

        # Check if there are partners to anonymize
        if not self.partner_ids:
            raise UserError(_("No partners selected for anonymization."))

    def action_confirm(self):
        """Confirm and process partner anonymization for multiple partners"""
        self.ensure_one()
        self._validate_partners_for_anonymization()

        for partner in self.partner_ids:
            partner.anonymize_partner_data()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Anonymization Result"),
                "message": _(
                    "%(partner_count)d partner(s) have been anonymized successfully."
                )
                % {"partner_count": len(self.partner_ids)},
                "sticky": False,
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
