# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PrivacyActivity(models.Model):
    _name = "privacy.activity"
    _description = "Data processing activities"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    active = fields.Boolean(
        default=True,
        index=True,
    )
    name = fields.Char(
        index=True,
        required=True,
        translate=True,
    )
    description = fields.Html(
        translate=True, help="How is personal data used here? Why? Etc."
    )
    controller_id = fields.Many2one(
        comodel_name="res.partner",
        string="Controller",
        required=True,
        default=lambda self: self._default_controller_id(),
        help="Whoever determines the purposes and means of the processing "
        "of personal data.",
    )
    processor_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="privacy_activity_res_partner_processor_ids",
        string="Processors",
        help="Whoever processes personal data on behalf of the controller.",
    )
    subject_find = fields.Boolean(
        string="Define subjects",
        help="Are affected subjects present in this database?",
    )
    subject_domain = fields.Char(
        string="Subjects filter",
        default="[]",
        help="Selection filter to find specific subjects included.",
    )

    @api.model
    def _default_controller_id(self):
        """By default it should be the current user's company."""
        return self.env.user.company_id.partner_id
