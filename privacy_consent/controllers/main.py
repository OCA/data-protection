# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from markupsafe import Markup
from werkzeug.exceptions import NotFound

from odoo.http import Controller, request, route
from odoo.tools import consteq


class ConsentController(Controller):
    @route(
        "/privacy/consent/<any(accept,reject):choice>/<int:consent_id>/<token>",
        type="http",
        auth="public",
        website=True,
    )
    def consent(self, choice, consent_id, token, *args, **kwargs):
        """Process user's consent acceptance or rejection."""
        consent = (
            request.env["privacy.consent"]
            .with_context(subject_answering=True)
            .sudo()
            .browse(consent_id)
        )
        if not (consent.exists() and consteq(consent._token(), token)):
            raise NotFound
        if consent.partner_id.lang:
            request.update_context(lang=consent.partner_id.lang)
        consent.action_answer(choice == "accept", self._metadata())
        return request.render(
            "privacy_consent.form",
            {
                "consent": consent,
                "controller_name_html": Markup(
                    consent.activity_id.controller_id.with_context(
                        show_address=True, html_format=True
                    ).name_get()[0][1]
                ),
            },
        )

    def _metadata(self):
        return (
            "User agent: {}\n" "Remote IP: {}\n" "Date and time: {:%Y-%m-%d %H:%M:%S}"
        ).format(
            request.httprequest.environ.get("HTTP_USER_AGENT"),
            request.httprequest.environ.get("REMOTE_ADDRESS"),
            datetime.now(),
        )
