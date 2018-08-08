# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from werkzeug.exceptions import NotFound

from odoo.http import Controller, request, route

from odoo.addons.web.controllers.main import ensure_db


class ConsentController(Controller):
    @route("/privacy/consent/<any(accept,reject):choice>/"
           "<int:consent_id>/<token>",
           type="http", auth="none", website=True)
    def consent(self, choice, consent_id, token, *args, **kwargs):
        """Process user's consent acceptance or rejection."""
        ensure_db()
        try:
            # If there's a website, we need a user to render the template
            request.uid = request.website.user_id.id
        except AttributeError:
            # If there's no website, the default is OK
            pass
        consent = request.env["privacy.consent"] \
            .with_context(subject_answering=True) \
            .sudo().browse(consent_id)
        if not (consent.exists() and consent._token() == token):
            raise NotFound
        if consent.partner_id.lang:
            consent = consent.with_context(lang=consent.partner_id.lang)
            request.context = consent.env.context
        consent.action_answer(choice == "accept", self._metadata())
        return request.render("privacy_consent.form", {
            "consent": consent,
        })

    def _metadata(self):
        return (u"User agent: {}\n"
                u"Remote IP: {}\n"
                u"Date and time: {:%Y-%m-%d %H:%M:%S}").format(
            request.httprequest.environ.get("HTTP_USER_AGENT"),
            request.httprequest.environ.get("REMOTE_ADDRESS"),
            datetime.now(),
        )
