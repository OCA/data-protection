# Copyright (C) 2025 Cetmix OÜ
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import _, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_anonymize_partner(self):
        """Open a wizard to confirm partner anonymization"""
        self.ensure_one()
        self = self.sudo()

        # Check access rights
        if not self.env.user.has_group(
            "privacy_partner_to_be_forgotten.group_partner_anonymize"
        ):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Access Denied"),
                    "message": _(
                        "You don't have permission to anonymize partners."
                    ),  # check text message according to task
                    "type": "warning",
                    "sticky": False,
                },
            }

        # Check if partner is a company
        if self.is_company:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Warning"),
                    "message": _(
                        "Company records cannot be anonymized."
                    ),  # check text message according to task
                    "type": "warning",
                    "sticky": False,
                },
            }

        # Check if partner is already anonymized
        if self.email and "@anonymized.oca" in self.email:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Warning"),
                    "message": _(
                        "This partner is already anonymized."
                    ),  # check text message according to task
                    "type": "warning",
                    "sticky": False,
                },
            }

        return {
            "type": "ir.actions.act_window",
            "name": _("Anonymize Partner"),
            "res_model": "partner.anonymize.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_partner_ids": [(6, 0, self.ids)]},
        }

    def anonymize_partner_data(self):
        """Anonymize partner personal data"""
        self.ensure_one()

        # Generate anonymized values
        now = datetime.datetime.now()
        date_stamp = now.strftime("%d.%m.%y")

        # Create initials from name
        name_parts = (self.name or "").split()
        initials = "".join(part[0].upper() for part in name_parts if part) or "X"

        anonymized_name = f"{initials} Anonymized"
        anonymized_email = f"{initials.lower()}_{date_stamp}_{self.id}@anonymized.oca"

        # Update partner data
        self.write(
            {
                "name": anonymized_name,
                "email": anonymized_email,
                "phone": False,
                "mobile": False,
                "street": False,
                "street2": False,
                "city": False,
                "state_id": False,
                "zip": False,
                "country_id": False,
                "function": False,
                "title": False,
                "vat": False,
                "ref": False,
                "comment": False,
                "website": False,
                "image_1920": False,
                "image_1024": False,
                "image_512": False,
                "image_256": False,
                "image_128": False,
                "active": False,
            }
        )

        # Anonymize linked user accounts
        self.user_ids.write(
            {
                "login": anonymized_email,
                "email": anonymized_email,
                "active": False,
                "signature": False,
            }
        )

        # Delete all messages related to this partner
        message_domain = [
            "|",
            "|",
            "|",
            # Messages where this partner is the referenced record
            "&",
            ("model", "=", "res.partner"),
            ("res_id", "=", self.id),
            # Messages created by this partner
            ("author_id", "=", self.id),
            # Messages where this partner is in recipients
            ("partner_ids", "in", [self.id]),
            # Messages in channels where this partner is a member
            "&",
            ("model", "=", "mail.channel"),
            (
                "res_id",
                "in",
                self.env["mail.channel"]
                .search([("channel_partner_ids", "in", self.id)])
                .ids,
            ),
        ]
        messages = self.env["mail.message"].sudo().search(message_domain)

        # Delete attachments
        attachment_domain = [
            "|",  # OR operator between two main conditions
            # Direct attachments on partner record
            "&",
            ("res_model", "=", "res.partner"),
            ("res_id", "=", self.id),
            # Attachments in all found messages
            "&",
            ("res_model", "=", "mail.message"),
            ("res_id", "in", messages.ids),
        ]
        attachments = self.env["ir.attachment"].sudo().search(attachment_domain)

        # Delete messages and attachments
        messages.unlink()
        attachments.unlink()

        # Add a log note about anonymization
        self.message_post(
            body=_("This contact has been anonymized on %(date)s by %(user)s")
            % {"date": now.strftime("%Y-%m-%d %H:%M:%S"), "user": self.env.user.name},
            subtype_id=self.env.ref("mail.mt_note").id,
        )

        return True
