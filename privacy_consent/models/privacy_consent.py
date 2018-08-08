# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import hmac

from odoo import api, fields, models


class PrivacyConsent(models.Model):
    _name = 'privacy.consent'
    _description = "Consent of data processing"
    _inherit = "mail.thread"
    _rec_name = "partner_id"
    _sql_constraints = [
        ("unique_partner_activity", "UNIQUE(partner_id, activity_id)",
         "Duplicated partner in this data processing activity"),
    ]

    active = fields.Boolean(
        default=True,
        index=True,
    )
    accepted = fields.Boolean(
        track_visibility="onchange",
        help="Indicates current acceptance status, which can come from "
             "subject's last answer, or from the default specified in the "
             "related data processing activity.",
    )
    last_metadata = fields.Text(
        readonly=True,
        track_visibility="onchange",
        help="Metadata from the last acceptance or rejection by the subject",
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Subject",
        required=True,
        readonly=True,
        track_visibility="onchange",
        help="Subject asked for consent.",
    )
    activity_id = fields.Many2one(
        "privacy.activity",
        "Activity",
        readonly=True,
        required=True,
        track_visibility="onchange",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("sent", "Awaiting response"),
            ("answered", "Answered"),
        ],
        default="draft",
        readonly=True,
        required=True,
        track_visibility="onchange",
    )

    def _track_subtype(self, init_values):
        """Return specific subtypes."""
        if self.env.context.get("subject_answering"):
            return "privacy_consent.mt_consent_acceptance_changed"
        if "activity_id" in init_values or "partner_id" in init_values:
            return "privacy_consent.mt_consent_consent_new"
        if "state" in init_values:
            return "privacy_consent.mt_consent_state_changed"
        return super(PrivacyConsent, self)._track_subtype(init_values)

    def _token(self):
        """Secret token to publicly authenticate this record."""
        secret = self.env["ir.config_parameter"].sudo().get_param(
            "database.secret")
        params = "{}-{}-{}-{}".format(
            self.env.cr.dbname,
            self.id,
            self.partner_id.id,
            self.activity_id.id,
        )
        return hmac.new(
            secret.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha512,
        ).hexdigest()

    def _url(self, accept):
        """Tokenized URL to let subject decide consent.

        :param bool accept:
            Indicates if you want the acceptance URL, or the rejection one.
        """
        return "/privacy/consent/{}/{}/{}?db={}".format(
            "accept" if accept else "reject",
            self.id,
            self._token(),
            self.env.cr.dbname,
        )

    def _send_consent_notification(self):
        """Send email notification to subject."""
        consents_by_template = {}
        for one in self.with_context(tpl_force_default_to=True,
                                     mail_notify_user_signature=False,
                                     mail_auto_subscribe_no_notify=True,
                                     mark_consent_sent=True):
            # Group consents by template, to send in batch where possible
            template_id = one.activity_id.consent_template_id.id
            consents_by_template.setdefault(template_id, one)
            consents_by_template[template_id] |= one
        # Send emails
        for template_id, consents in consents_by_template.items():
            consents.message_post_with_template(
                template_id,
                # This mode always sends email, regardless of partner's
                # notification preferences; we use it here because it's very
                # likely that we are asking authorisation to send emails
                composition_mode="mass_mail",
            )

    def _run_action(self):
        """Execute server action defined in data processing activity."""
        for one in self:
            # Always skip draft consents
            if one.state == "draft":
                continue
            action = one.activity_id.server_action_id.with_context(
                active_id=one.id,
                active_ids=one.ids,
                active_model=one._name,
            )
            action.run()

    @api.model
    def create(self, vals):
        """Run server action on create."""
        result = super(PrivacyConsent, self).create(vals)
        # Sync the default acceptance status
        result.sudo()._run_action()
        return result

    def write(self, vals):
        """Run server action on update."""
        result = super(PrivacyConsent, self).write(vals)
        self._run_action()
        return result

    def message_get_suggested_recipients(self):
        result = super(PrivacyConsent, self) \
            .message_get_suggested_recipients()
        reason = self._fields["partner_id"].string
        for one in self:
            one._message_add_suggested_recipient(
                result,
                partner=one.partner_id,
                reason=reason,
            )
        return result

    def action_manual_ask(self):
        """Let user manually ask for consent."""
        return {
            "context": {
                "default_composition_mode": "mass_mail",
                "default_model": self._name,
                "default_res_id": self.id,
                "default_template_id": self.activity_id.consent_template_id.id,
                "default_use_template": True,
                "mark_consent_sent": True,
                "tpl_force_default_to": True,
            },
            "force_email": True,
            "res_model": "mail.compose.message",
            "target": "new",
            "type": "ir.actions.act_window",
            "view_mode": "form",
        }

    def action_auto_ask(self):
        """Automatically ask for consent."""
        templated = self.filtered("activity_id.consent_template_id")
        automated = templated.filtered(
            lambda one: one.activity_id.consent_required == "auto")
        automated._send_consent_notification()

    def action_answer(self, answer, metadata=False):
        """Process answer.

        :param bool answer:
            Did the subject accept?

        :param str metadata:
            Metadata from last user acceptance or rejection request.
        """
        self.write({
            "state": "answered",
            "accepted": answer,
            "last_metadata": metadata,
        })
