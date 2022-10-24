# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import html

from odoo import _, api, models
from odoo.exceptions import ValidationError


class MailTemplate(models.Model):
    _inherit = "mail.template"

    @api.constrains("body_html", "model")
    def _check_consent_links_in_body_html(self):
        """Body for ``privacy.consent`` templates needs placeholder links."""
        links = [
            "//a[@href='/privacy/consent/{}/']".format(action)
            for action in ("accept", "reject")
        ]
        for one in self:
            if one.model != "privacy.consent":
                continue
            doc = html.document_fromstring(one.body_html)
            for link in links:
                if not doc.xpath(link):
                    raise ValidationError(
                        _(
                            "Missing privacy consent link placeholders. "
                            "You need at least these two links:\n"
                            '<a href="%(consent_url)s">Accept</a>\n'
                            '<a href="%(reject_url)s">Reject</a>',
                            consent_url="/privacy/consent/accept/",
                            reject_url="/privacy/consent/reject/",
                        )
                    )
