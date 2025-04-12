# Copyright (C) 2025 Cetmix OÜ
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import _, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def anonymize_partner_data(self):
        """Anonymizes personally identifiable information for a res.partner record.

        Implements GDPR data erasure requirements by anonymizing all personal data.

        This includes:
        - Replacing name with anonymized initials (e.g., "EC Anonymized")
        - Creating unique anonymized email with date stamp
        - Clearing contact fields (phone, address, website, job title, tax ID)
        - Clearing notes, references, and avatars
        - Archiving partner record (active=False)

        Additionally:
        - Anonymizes linked res.users (login/email) and archives them
        - Removes all mail.message chatter logs
        - Removes all ir.attachment files from partner/messages
        - Adds anonymization log note

        Note: This operation is irreversible and removes all personal data traces.
        """
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
            ("model", "=", "discuss.channel"),
            (
                "res_id",
                "in",
                self.env["discuss.channel"]
                .search([("channel_member_ids.partner_id", "=", self.id)])
                .ids,
            ),
        ]
        messages = self.env["mail.message"].sudo().search(message_domain)

        # Delete attachments
        attachment_domain = [
            "|",
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
