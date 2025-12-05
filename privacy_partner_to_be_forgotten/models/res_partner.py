# Copyright (C) 2025 Cetmix OÜ
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import logging

from odoo import _, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_partner_initials(self):
        """Generate initials from partner name."""
        name_parts = (self.name or "").split()
        initials = "".join(part[0].upper() for part in name_parts if part)
        return initials or "X"

    def _generate_anonymized_email(self, initials):
        """Generate anonymized email address.

        Args:
            initials (str): Partner name initials (e.g., "JD" for "John Doe")

        Returns:
            str: Anonymized email address in format
                "initials_yyyy-mm-dd_id@anonymized.oca"
        """
        date_stamp = fields.Date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        return f"{initials.lower()}_{date_stamp}_{self.id}@anonymized.oca"

    def _prepare_company_anonymized_vals(self, anonymized_name):
        """Prepare values for anonymizing company data.

        For companies, we only anonymize the name by adding 'Anonymized' suffix
        and set active to False, while preserving all business-critical information.

        Args:
            anonymized_name (str): Generated anonymous name for the company
                (format: "Company Name Anonymized")

        Returns:
            dict: Dictionary of fields to update with anonymized values
        """
        return {
            "name": anonymized_name,
            "active": False,
        }

    def _prepare_partner_anonymized_vals(self, anonymized_name, anonymized_email):
        """Prepare values for anonymizing partner data.

        Args:
            anonymized_name (str): Generated anonymous name for the partner
                (format: "XX Anonymized")
            anonymized_email (str): Generated anonymous email
                (format: "xx_dd.mm.yy_id@anonymized.oca")

        Returns:
            dict: Dictionary of fields to update with anonymized or cleared values
        """
        return {
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

    def _prepare_user_anonymized_vals(self, anonymized_email):
        """Prepare values for anonymizing related user accounts.

        Args:
            anonymized_email (str): Generated anonymous email
                (format: "xx_dd.mm.yy_id@anonymized.oca")

        Returns:
            dict: Dictionary containing user fields to update
                (login, email, active status, signature)
        """
        return {
            "login": anonymized_email,
            "email": anonymized_email,
            "active": False,
            "signature": False,
        }

    def _anonymize_user(self, anonymized_email=False):
        """Anonymize related user accounts.

        Args:
            anonymized_email (str, optional): Generated anonymous email to be set
                for user accounts. Only needed for individual contacts.
        """
        if self.user_ids:
            if self.is_company:
                vals = {"active": False}
            else:
                vals = self._prepare_user_anonymized_vals(anonymized_email)
            self.user_ids.with_context(tracking_disable=True).write(vals)

    def _anonymize_partner(self, anonymized_name, anonymized_email):
        """Anonymize partner record."""
        # Setting active_test=True ensures that search() operations filter by
        # active=True. This is needed because Odoo prevents archiving users with
        # non-archived partners, and the partner archiving check is done via a regular
        # search() that doesn't filter archived records when active_test=False
        self.with_context(
            active_test=True,
            tracking_disable=True,
        ).write(
            self._prepare_partner_anonymized_vals(anonymized_name, anonymized_email)
        )

    def _get_messages_domain(self):
        """Prepare domain for searching messages to be deleted during anonymization."""
        return [
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

    def _anonymize_partner_messages(self):
        """Delete all messages related to this partner."""
        messages = self.env["mail.message"].sudo().search(self._get_messages_domain())
        _logger.info(
            "Anonymizing partner %s (ID: %s): Removing %s messages",
            self.name,
            self.id,
            len(messages),
        )
        if not messages:
            return

        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "mail.message/delete",
            {"message_ids": messages.ids},
        )
        messages.unlink()

    def _get_attachments_domain(self):
        """Prepare domain for searching attachments to be deleted during
        anonymization.
        """
        self.ensure_one()
        return [
            ("res_model", "=", "res.partner"),
            ("res_id", "=", self.id),
        ]

    def _anonymize_partner_attachments(self):
        """Delete all attachments related to partner."""
        attachments = (
            self.env["ir.attachment"].sudo().search(self._get_attachments_domain())
        )
        _logger.info(
            "Anonymizing partner %s (ID: %s): Removing %s attachments",
            self.name,
            self.id,
            len(attachments),
        )
        if not attachments:
            return

        updates = [
            (self.env.user.partner_id, "ir.attachment/delete", {"id": attachment.id})
            for attachment in attachments
        ]
        for update in updates:
            self.env["bus.bus"]._sendone(*update)
        attachments.unlink()

    def _log_anonymization(self, timestamp):
        """Log anonymization action in chatter."""
        message = self.message_post(
            body=_(
                "This contact has been anonymized on %(date)s by %(user)s",
                date=fields.Datetime.to_string(timestamp),
                user=self.env.user.name,
            ),
            subtype_xmlid="mail.mt_note",
        )

        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "mail.record/insert",
            {
                "Message": {
                    "id": message.id,
                    "body": message.body,
                }
            },
        )

    def anonymize_partner_data(self):
        """Anonymize partner and all related data.

        Executes anonymization in the following steps:
        1. Generates anonymized identifiers
        2. Anonymizes related user accounts
        3. Anonymizes partner record
        4. Removes related messages
        5. Removes related attachments
        6. Logs the anonymization action

        Note: This operation is irreversible and removes all personal data traces.
        """
        self.ensure_one()
        now = fields.Datetime.now()

        if self.is_company:
            # Company anonymization
            anonymized_name = _("%(company)s Anonymized", company=self.name)
            self._anonymize_user()
            self.with_context(active_test=True, tracking_disable=True).write(
                self._prepare_company_anonymized_vals(anonymized_name)
            )
        else:
            # Individual contact anonymization
            initials = self._get_partner_initials()
            anonymized_name = _("%(initials)s Anonymized", initials=initials)
            anonymized_email = self._generate_anonymized_email(initials)

            self._anonymize_user(anonymized_email)
            self._anonymize_partner(anonymized_name, anonymized_email)

        # Common operations for both companies and individuals
        self._anonymize_partner_messages()
        self._anonymize_partner_attachments()
        self._log_anonymization(now)

        return True
