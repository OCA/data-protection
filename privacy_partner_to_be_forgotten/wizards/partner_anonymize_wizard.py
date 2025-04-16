# Copyright (C) 2025 Cetmix OÜ
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
            domain = [("id", "child_of", active_ids)]
            all_partners = self.env["res.partner"].search(domain)
            res["partner_ids"] = [(6, 0, all_partners.ids)]
        return res

    def _validate_partners_for_anonymization(self):
        # Check access rights
        if not self.env.user.has_group(
            "privacy_partner_to_be_forgotten.group_partner_anonymize"
        ):
            raise AccessError(_("You don't have permission to anonymize partners."))

        # Check if partner is a company
        company_partners = self.partner_ids.filtered("is_company")
        if company_partners:
            company_names = ", ".join(company_partners.mapped("name"))
            raise UserError(
                _("Cannot anonymize the following company records: %s") % company_names
            )

        # Check if partner is already anonymized
        anonymized_partners = self.partner_ids.filtered(
            lambda p: p.email and "@anonymized.oca" in p.email
        )
        if anonymized_partners:
            anonymized_names = ", ".join(anonymized_partners.mapped("name"))
            raise UserError(
                _("The following partners are already anonymized: %s")
                % anonymized_names
            )

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
                "message": _("%d partner(s) have been anonymized successfully.")
                % len(self.partner_ids),
                "sticky": False,
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
