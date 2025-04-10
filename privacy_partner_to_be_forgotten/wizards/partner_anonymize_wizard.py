from odoo import _, fields, models


class PartnerAnonymizeWizard(models.TransientModel):
    _name = "partner.anonymize.wizard"
    _description = "Partner Anonymization Wizard"

    partner_ids = fields.Many2many(
        "res.partner",
        string="Partners",
        required=True,
        readonly=True,
    )

    def action_confirm(self):
        """Confirm and process partner anonymization for multiple partners"""
        self.ensure_one()
        company_partners = self.partner_ids.filtered(lambda p: p.is_company)
        partners_to_anonymize = self.partner_ids - company_partners

        # Show warning if company partners were selected
        if company_partners:
            company_names = ", ".join(company_partners.mapped("name"))
            self.env["bus.bus"]._sendone(
                self.env.user.partner_id,
                "warning",
                {
                    "title": _("Warning"),
                    "message": _("These company records cannot be anonymized: %s")
                    % company_names,
                },
            )

        # Process anonymization for valid partners
        for partner in partners_to_anonymize:
            partner.anonymize_partner_data()

        anonymized_count = len(partners_to_anonymize)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("%s partner(s) have been anonymized successfully.")
                % anonymized_count,
                "type": "success",
                "sticky": False,
            },
        }
