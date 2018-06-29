# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    privacy_consent_ids = fields.One2many(
        "privacy.consent",
        "partner_id",
        "Privacy consents",
    )
    privacy_consent_ids_count = fields.Integer(
        "Consents",
        compute="_compute_privacy_consent_ids_count",
        help="Privacy consent requests amount",
    )

    @api.depends("privacy_consent_ids")
    def _compute_privacy_consent_ids_count(self):
        """Count consent requests."""
        groups = self.env["privacy.consent"].read_group(
            [("partner_id", "in", self.ids)],
            ["partner_id"],
            ["partner_id"],
        )
        for group in groups:
            self.browse(group["partner_id"], self._prefetch) \
                .privacy_consent_ids_count = group["__count"]
