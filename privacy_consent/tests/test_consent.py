# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager

from odoo.exceptions import ValidationError
from odoo.tests.common import HttpCase, Form


class ActivityCase(HttpCase):
    def setUp(self):
        super(ActivityCase, self).setUp()
        self.cron = self.env.ref("privacy_consent.cron_auto_consent")
        self.cron_mail_queue = self.env.ref(
            "mail.ir_cron_mail_scheduler_action")
        self.sync_blacklist = self.env.ref("privacy_consent.sync_blacklist")
        self.mt_consent_consent_new = self.env.ref(
            "privacy_consent.mt_consent_consent_new")
        self.mt_consent_acceptance_changed = self.env.ref(
            "privacy_consent.mt_consent_acceptance_changed")
        self.mt_consent_state_changed = self.env.ref(
            "privacy_consent.mt_consent_state_changed")
        # Some partners to ask for consent
        self.partners = self.env["res.partner"]
        self.partners += self.partners.create({
            "name": "consent-partner-0",
            "email": "partner0@example.com",
        })
        self.partners += self.partners.create({
            "name": "consent-partner-1",
            "email": "partner1@example.com",
        })
        self.partners += self.partners.create({
            "name": "consent-partner-2",
            "email": "partner2@example.com",
        })
        # Partner without email, on purpose
        self.partners += self.partners.create({
            "name": "consent-partner-3",
        })
        # Partner with wrong email, on purpose
        self.partners += self.partners.create({
            "name": "consent-partner-4",
            "email": "wrong-mail",
        })
        # Blacklist some partners
        self.blacklists = self.env["mail.blacklist"]
        self.blacklists += self.blacklists._add("partner1@example.com")
        # Activity without consent
        self.activity_noconsent = self.env["privacy.activity"].create({
            "name": "activity_noconsent",
            "description": "I'm activity 1",
        })
        # Activity with auto consent, for all partners
        self.activity_auto = self.env["privacy.activity"].create({
            "name": "activity_auto",
            "description": "I'm activity auto",
            "subject_find": True,
            "subject_domain": repr([("id", "in", self.partners.ids)]),
            "consent_required": "auto",
            "default_consent": True,
            "server_action_id": self.sync_blacklist.id,
        })
        # Activity with manual consent, skipping partner 0
        self.activity_manual = self.env["privacy.activity"].create({
            "name": "activity_manual",
            "description": "I'm activity 3",
            "subject_find": True,
            "subject_domain": repr([("id", "in", self.partners[1:].ids)]),
            "consent_required": "manual",
            "default_consent": False,
            "server_action_id": self.sync_blacklist.id,
        })

    @contextmanager
    def _patch_build(self):
        self._built_messages = []
        IMS = self.env['ir.mail_server']

        def _build_email(
            _self,
            email_from,
            email_to,
            subject,
            body,
            *args,
            **kwargs
        ):
            self._built_messages.append(body)
            return _build_email.origin(
                _self,
                email_from,
                email_to,
                subject,
                body,
                *args,
                **kwargs,
            )

        try:
            IMS._patch_method('build_email', _build_email)
            yield
        finally:
            IMS._revert_method('build_email')

    def check_activity_auto_properly_sent(self):
        """Check emails sent by ``self.activity_auto``."""
        consents = self.env["privacy.consent"].search([
            ("activity_id", "=", self.activity_auto.id),
        ])
        # Check pending mails
        for consent in consents:
            self.assertEqual(consent.state, "draft")
            messages = consent.message_ids
            self.assertEqual(len(messages), 2)
        # Check sent mails
        with self._patch_build():
            self.cron_mail_queue.method_direct_trigger()
        for index, consent in enumerate(consents):
            good_email = "@" in (consent.partner_id.email or "")
            expected_messages = 3 if good_email else 2
            self.assertEqual(
                consent.state,
                "sent" if good_email else "draft",
            )
            messages = consent.message_ids
            self.assertEqual(len(messages), expected_messages)
            # 2nd message notifies creation
            self.assertEqual(
                messages[expected_messages - 1].subtype_id,
                self.mt_consent_consent_new,
            )
            # 3rd message notifies subject
            # Placeholder links should be logged
            self.assertIn(
                "/privacy/consent/accept/",
                messages[expected_messages - 2].body)
            self.assertIn(
                "/privacy/consent/reject/",
                messages[expected_messages - 2].body)
            # Tokenized links shouldn't be logged
            self.assertNotIn(
                consent._url(True),
                messages[expected_messages - 2].body)
            self.assertNotIn(
                consent._url(False),
                messages[expected_messages - 2].body)
            # 4th message contains the state change
            if good_email:
                self.assertEqual(
                    messages[0].subtype_id,
                    self.mt_consent_state_changed,
                )
            # Partner's is_blacklisted should be synced with default consent
            self.assertFalse(consent.partner_id.is_blacklisted)
            # Check the sent message was built properly tokenized
            accept_url, reject_url = map(consent._url, (True, False))
            for body in self._built_messages:
                if accept_url in body and reject_url in body:
                    self._built_messages.remove(body)
                    break
            else:
                raise AssertionError("Some message body should have these urls")

    def test_default_template(self):
        """We have a good mail template by default."""
        good = self.env.ref("privacy_consent.template_consent")
        self.assertEqual(
            self.activity_noconsent.consent_template_id,
            good,
        )
        self.assertEqual(
            self.activity_noconsent.consent_template_default_body_html,
            good.body_html,
        )
        self.assertEqual(
            self.activity_noconsent.consent_template_default_subject,
            good.subject,
        )

    def test_find_subject_if_consent_required(self):
        """If user wants to require consent, it needs subjects."""
        # Test the onchange helper
        onchange_activity1 = self.env["privacy.activity"].new(
            self.activity_noconsent.copy_data()[0])
        self.assertFalse(onchange_activity1.subject_find)
        onchange_activity1.consent_required = "auto"
        onchange_activity1._onchange_consent_required_subject_find()
        self.assertTrue(onchange_activity1.subject_find)
        # Test very dumb user that forces an error
        with self.assertRaises(ValidationError):
            self.activity_noconsent.consent_required = "manual"

    def test_template_required_auto(self):
        """Automatic consent activities need a template."""
        self.activity_noconsent.subject_find = True
        self.activity_noconsent.consent_template_id = False
        self.activity_noconsent.consent_required = "manual"
        with self.assertRaises(ValidationError):
            self.activity_noconsent.consent_required = "auto"

    def test_generate_manually(self):
        """Manually-generated consents work as expected."""
        for partner in self.partners:
            if "@" in (partner.email or ""):
                self.blacklists._remove(partner.email)
        result = self.activity_manual.action_new_consents()
        self.assertEqual(result["res_model"], "privacy.consent")
        consents = self.env[result["res_model"]].search(result["domain"])
        self.assertEqual(consents.mapped("state"), ["draft"] * 3)
        self.assertEqual(
            consents.mapped("partner_id.is_blacklisted"),
            [False] * 3,
        )
        self.assertEqual(consents.mapped("accepted"), [False] * 3)
        self.assertEqual(consents.mapped("last_metadata"), [False] * 3)
        # Check sent mails
        messages = consents.mapped("message_ids")
        self.assertEqual(len(messages), 3)
        subtypes = messages.mapped("subtype_id")
        self.assertTrue(subtypes & self.mt_consent_consent_new)
        self.assertFalse(subtypes & self.mt_consent_acceptance_changed)
        self.assertFalse(subtypes & self.mt_consent_state_changed)
        # Send one manual request
        action = consents[0].action_manual_ask()
        self.assertEqual(action["res_model"], "mail.compose.message")
        Composer = self.env[action["res_model"]].with_context(
            active_ids=consents[0].ids,
            active_model=consents._name,
            **action["context"],
        )
        composer_wizard = Form(Composer)
        self.assertIn(consents[0].partner_id.name, composer_wizard.body)
        composer_record = composer_wizard.save()
        with self._patch_build():
            composer_record.send_mail()
        # Check the sent message was built properly tokenized
        body = self._built_messages[0]
        self.assertIn(consents[0]._url(True), body)
        self.assertIn(consents[0]._url(False), body)
        messages = consents.mapped("message_ids") - messages
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].subtype_id, self.mt_consent_state_changed)
        self.assertEqual(consents.mapped("state"), ["sent", "draft", "draft"])
        self.assertEqual(
            consents.mapped("partner_id.is_blacklisted"),
            [True, False, False],
        )
        # Placeholder links should be logged
        self.assertTrue("/privacy/consent/accept/" in messages[1].body)
        self.assertTrue("/privacy/consent/reject/" in messages[1].body)
        # Tokenized links shouldn't be logged
        accept_url = consents[0]._url(True)
        reject_url = consents[0]._url(False)
        self.assertNotIn(accept_url, messages[1].body)
        self.assertNotIn(reject_url, messages[1].body)
        # Visit tokenized accept URL
        result = self.url_open(accept_url).text
        self.assertIn("accepted", result)
        self.assertIn(reject_url, result)
        self.assertIn(self.activity_manual.name, result)
        self.assertIn(self.activity_manual.description, result)
        consents.invalidate_cache()
        self.assertEqual(consents.mapped("accepted"), [True, False, False])
        self.assertTrue(consents[0].last_metadata)
        self.assertFalse(consents[0].partner_id.is_blacklisted)
        self.assertEqual(
            consents.mapped("state"), ["answered", "draft", "draft"])
        self.assertEqual(
            consents[0].message_ids[0].subtype_id,
            self.mt_consent_acceptance_changed,
        )
        # Visit tokenized reject URL
        result = self.url_open(reject_url).text
        self.assertIn("rejected", result)
        self.assertIn(accept_url, result)
        self.assertIn(self.activity_manual.name, result)
        self.assertIn(self.activity_manual.description, result)
        consents.invalidate_cache()
        self.assertEqual(consents.mapped("accepted"), [False, False, False])
        self.assertTrue(consents[0].last_metadata)
        self.assertTrue(consents[0].partner_id.is_blacklisted)
        self.assertEqual(
            consents.mapped("state"), ["answered", "draft", "draft"])
        self.assertEqual(
            consents[0].message_ids[0].subtype_id,
            self.mt_consent_acceptance_changed,
        )
        self.assertFalse(consents[1].last_metadata)

    def test_generate_automatically(self):
        """Automatically-generated consents work as expected."""
        result = self.activity_auto.action_new_consents()
        self.assertEqual(result["res_model"], "privacy.consent")
        self.check_activity_auto_properly_sent()

    def test_generate_cron(self):
        """Cron-generated consents work as expected."""
        self.cron.method_direct_trigger()
        self.check_activity_auto_properly_sent()

    def test_mail_template_without_links(self):
        """Cannot create mail template without needed links."""
        with self.assertRaises(ValidationError):
            self.activity_manual.consent_template_id.body_html = "No links :("
