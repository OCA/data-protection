# Copyright 2018 Tecnativa - Jairo Llopis
# Copyright 2026 fidpa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from markupsafe import Markup
from werkzeug.exceptions import NotFound

from odoo.http import Controller, request, route
from odoo.tools import consteq

# The consent pages carry an authenticating token in their URL. Deny framing
# so the explicit-submit guarantee cannot be defeated by clickjacking (UI
# redress) of the confirmation form.
SECURITY_HEADERS = [
    ("X-Frame-Options", "DENY"),
    ("Content-Security-Policy", "frame-ancestors 'none'"),
]


class ConsentController(Controller):
    @route(
        "/privacy/consent/<any(accept,reject):choice>/<int:consent_id>/<token>",
        type="http",
        auth="public",
        methods=["GET", "POST"],
        website=True,
        csrf=False,
    )
    def consent(self, choice, consent_id, token, *args, **kwargs):
        """Ask for confirmation (GET) and process the answer (POST).

        The answer is recorded only on an explicit POST: mail gateways
        and antivirus link scanners prefetch every URL found in an
        e-mail with GET requests, and every consent e-mail contains both
        the accept and the reject link, so recording on GET stored false
        answers chosen effectively at random by such scanners.

        CSRF protection is disabled on purpose: the HMAC token in the
        URL is the credential that authorizes the answer, so a CSRF
        attacker would need to know the token, in which case they could
        POST directly anyway. Requiring the session-bound CSRF token
        would only break subjects whose browsers block cookies.
        """
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
        accepting = choice == "accept"
        values = {
            "consent": consent,
            "controller_name_html": Markup(
                consent.activity_id.controller_id.with_context(
                    show_address=True, html_format=True
                ).display_name
            ),
        }
        if request.httprequest.method != "POST":
            values.update(
                accepting=accepting,
                form_action=request.httprequest.full_path,
            )
            return request.render(
                "privacy_consent.confirm", values, headers=list(SECURITY_HEADERS)
            )
        consent.action_answer(accepting, self._metadata())
        return request.render(
            "privacy_consent.form", values, headers=list(SECURITY_HEADERS)
        )

    def _metadata(self):
        return (
            "User agent: {}\n" "Remote IP: {}\n" "Date and time: {:%Y-%m-%d %H:%M:%S}"
        ).format(
            request.httprequest.environ.get("HTTP_USER_AGENT"),
            request.httprequest.environ.get("REMOTE_ADDR"),
            datetime.now(),
        )
