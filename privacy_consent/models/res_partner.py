# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    privacy_consent_ids = fields.One2many(
        comodel_name="privacy.consent",
        inverse_name="partner_id",
        string="Privacy consents",
    )
    privacy_consent_count = fields.Integer(
        string="Consents",
        compute="_compute_privacy_consent_count",
        help="Privacy consent requests amount",
    )

    @api.depends("privacy_consent_ids")
    def _compute_privacy_consent_count(self):
        """Count consent requests."""
        groups = self.env["privacy.consent"]._read_group(
            [("partner_id", "in", self.ids)],
            ["partner_id"],
            ["__count"],
        )
        mapping = {partner.id: count for partner, count in groups}
        for one in self:
            one.privacy_consent_count = mapping.get(one.id, 0)
