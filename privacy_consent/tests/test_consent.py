# Copyright 2018 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from unittest.mock import patch

import requests

import odoo.tests
from odoo import http
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, users

from odoo.addons.base.models.ir_mail_server import IrMailServer
from odoo.addons.mail.tests.common import mail_new_test_user


class ActivityCase(odoo.tests.HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cron = cls.env.ref("privacy_consent.cron_auto_consent")
        cls.cron_mail_queue = cls.env.ref("mail.ir_cron_mail_scheduler_action")
        cls.sync_blacklist = cls.env.ref("privacy_consent.sync_blacklist")
        cls.mt_consent_consent_new = cls.env.ref(
            "privacy_consent.mt_consent_consent_new"
        )
        cls.mt_consent_acceptance_changed = cls.env.ref(
            "privacy_consent.mt_consent_acceptance_changed"
        )
        cls.mt_consent_state_changed = cls.env.ref(
            "privacy_consent.mt_consent_state_changed"
        )
        # Some partners to ask for consent
        cls.partners = cls.env["res.partner"].create(
            [
                {"name": "consent-partner-0", "email": "partner0@example.com"},
                {"name": "consent-partner-1", "email": "partner1@example.com"},
                {"name": "consent-partner-2", "email": "partner2@example.com"},
                # Partner without email, on purpose
                {"name": "consent-partner-3"},
                # Partner with wrong email, on purpose
                {"name": "consent-partner-4", "email": "wrong-mail"},
            ]
        )
        # Blacklist some partners
        cls.blacklists = cls.env["mail.blacklist"]
        cls.blacklists += cls.blacklists._add("partner1@example.com")
        # Activity without consent
        cls.activity_noconsent = cls.env["privacy.activity"].create(
            {"name": "activity_noconsent", "description": "I'm activity 1"}
        )
        # Activity with auto consent, for all partners
        cls.activity_auto = cls.env["privacy.activity"].create(
            {
                "name": "activity_auto",
                "description": "I'm activity auto",
                "subject_find": True,
                "subject_domain": repr([("id", "in", cls.partners.ids)]),
                "consent_required": "auto",
                "default_consent": True,
                "server_action_id": cls.sync_blacklist.id,
            }
        )
        # Activity with manual consent, skipping partner 0
        cls.activity_manual = cls.env["privacy.activity"].create(
            {
                "name": "activity_manual",
                "description": "I'm activity 3",
                "subject_find": True,
                "subject_domain": repr([("id", "in", cls.partners[1:].ids)]),
                "consent_required": "manual",
                "default_consent": False,
                "server_action_id": cls.sync_blacklist.id,
            }
        )

    @contextmanager
    def _patch_build(self):
        build_email_origin = IrMailServer.build_email
        self._built_messages = []

        def _build_email(_self, email_from, email_to, subject, body, *args, **kwargs):
            self._built_messages.append(body)
            return build_email_origin(
                _self, email_from, email_to, subject, body, *args, **kwargs
            )

        with patch.object(
            IrMailServer,
            "build_email",
            autospec=True,
            wraps=build_email_origin,
            side_effect=_build_email,
        ) as build_email_mocked:
            self.build_email_mocked = build_email_mocked
            yield


@odoo.tests.tagged("post_install", "-at_install")
class ActivityFlow(ActivityCase):
    def check_activity_auto_properly_sent(self):
        """Check emails sent by ``self.activity_auto``."""
        # Check message if model is not privacy.consent
        message = self.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": self.partners[0].id,
                "body": "Test message.",
                "subtype_id": self.mt_consent_consent_new.id,
            }
        )
        self.assertFalse("/privacy/consent/accept/" in message.body)
        self.assertFalse("/privacy/consent/reject/" in message.body)
        # Check pending mails
        for consent in self.activity_auto.consent_ids:
            self.assertEqual(consent.state, "draft")
            self.assertEqual(len(consent.message_ids), 2)
        # Check sent mails
        with self._patch_build():
            self.cron_mail_queue.method_direct_trigger()
        for consent in self.activity_auto.consent_ids:
            good_email = "@" in (consent.partner_id.email or "")
            self.assertEqual(
                consent.state,
                "sent" if good_email else "draft",
            )
            self.assertEqual(len(consent.message_ids), 2)
            # message notifies creation
            self.assertTrue(
                self.mt_consent_consent_new in consent.message_ids.mapped("subtype_id")
            )
            # message notifies subject
            # Placeholder links should be logged
            message_subject = consent.message_ids.filtered(
                lambda x: x.subtype_id != self.mt_consent_consent_new
            )
            self.assertIn("/privacy/consent/accept/", message_subject.body)
            self.assertIn("/privacy/consent/reject/", message_subject.body)
            # Tokenized links shouldn't be logged
            self.assertNotIn(consent._url(True), message_subject.body)
            self.assertNotIn(consent._url(False), message_subject.body)
            # without state change (only in test mode)
            self.assertTrue(
                self.mt_consent_state_changed
                not in consent.message_ids.mapped("subtype_id")
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

    def check_activity_auto_properly_sent_no_links(self):
        """Test case where no message contains the required URLs."""
        self.env["privacy.consent"].create(
            {
                "activity_id": self.activity_auto.id,
                "partner_id": self.partners[0].id,
                "state": "draft",
            }
        )
        self._built_messages = ["Random message without URLs"]
        with self.assertRaises(
            AssertionError, msg="Some message body should have these urls"
        ):
            self.activity_auto.check_activity_auto_properly_sent()

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
            self.activity_noconsent.copy_data()[0]
        )
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
            ids=consents[0].ids,
            model=consents._name,
            **action["context"],
        )
        composer_wizard = Form(Composer)
        self.assertIn(consents[0].partner_id.name, composer_wizard.body)
        composer_record = composer_wizard.save()
        with self._patch_build():
            composer_record.action_send_mail()
        # Check the sent message was built properly tokenized
        body = self._built_messages[0]
        self.assertIn(consents[0]._url(True), body)
        self.assertIn(consents[0]._url(False), body)
        messages = consents.mapped("message_ids") - messages
        self.assertEqual(len(messages), 1)
        self.assertNotEqual(messages.subtype_id, self.mt_consent_state_changed)
        self.assertEqual(consents.mapped("state"), ["sent", "draft", "draft"])
        self.assertEqual(
            consents.mapped("partner_id.is_blacklisted"),
            [True, False, False],
        )
        # Placeholder links should be logged
        self.assertTrue("/privacy/consent/accept/" in messages.body)
        self.assertTrue("/privacy/consent/reject/" in messages.body)
        # Tokenized links shouldn't be logged
        accept_url = consents[0]._url(True)
        reject_url = consents[0]._url(False)
        self.assertNotIn(accept_url, messages.body)
        self.assertNotIn(reject_url, messages.body)
        # Visit tokenized accept URL
        self.authenticate("portal", "portal")
        http.root.session_store.save(self.session)
        result = self.url_open(accept_url).text
        self.assertIn("accepted", result)
        self.assertIn(reject_url, result)
        self.assertIn(self.activity_manual.name, result)
        self.assertIn(self.activity_manual.description, result)
        consents.invalidate_recordset()
        self.assertEqual(consents.mapped("accepted"), [True, False, False])
        self.assertTrue(consents[0].last_metadata)
        self.assertFalse(consents[0].partner_id.is_blacklisted)
        self.assertEqual(consents.mapped("state"), ["answered", "draft", "draft"])
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
        consents.invalidate_recordset()
        self.assertEqual(consents.mapped("accepted"), [False, False, False])
        self.assertTrue(consents[0].last_metadata)
        self.assertTrue(consents[0].partner_id.is_blacklisted)
        self.assertEqual(consents.mapped("state"), ["answered", "draft", "draft"])
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

    def test_track_subtype(self):
        """Test that _track_subtype returns the correct
        mail message subtype for consent."""
        consent = self.env["privacy.consent"].create(
            {
                "activity_id": self.activity_auto.id,
                "partner_id": self.partners[0].id,
                "state": "draft",
            }
        )
        # Case 1: Change in state
        subtype = consent._track_subtype({"state": "approved"})
        self.assertEqual(
            subtype,
            self.env.ref("privacy_consent.mt_consent_state_changed"),
            "Subtype must be 'mt_consent_state_changed' when state is changed.",
        )
        # Case 2: Context subject_answering activated
        subtype = consent.with_context(subject_answering=True)._track_subtype({})
        self.assertEqual(
            subtype,
            self.env.ref("privacy_consent.mt_consent_acceptance_changed"),
            """Subtype must be 'mt_consent_acceptance_changed'
             when subject_answering is activated.""",
        )
        # Case 3: Without any of the conditions
        with patch.object(
            type(consent), "_track_subtype", return_value="super_subtype"
        ) as mock_super:
            subtype = consent._track_subtype({})
            mock_super.assert_called_once_with({})
            self.assertEqual(
                subtype,
                "super_subtype",
                "Subtype must be the same from original method.",
            )

    def test_message_get_suggested_recipients(self):
        """Test that consent suggests the correct recipients."""
        consent = self.env["privacy.consent"].create(
            {
                "activity_id": self.activity_auto.id,
                "partner_id": self.partners[0].id,
                "state": "draft",
            }
        )
        suggested_recipients = consent._message_get_suggested_recipients()
        recipient = suggested_recipients[0]
        self.assertEqual(consent.partner_id.id, recipient["partner_id"])
        self.assertIn(consent.partner_id.name, recipient["name"])
        self.assertIn(consent.partner_id.email, recipient["email"])

    def test_compute_consent_count(self):
        """Test that consent_count is correctly updated."""
        self.assertEqual(
            self.activity_auto.consent_count, 0, "Initial consent count should be 0."
        )
        self.env["privacy.consent"].create(
            {
                "activity_id": self.activity_auto.id,
                "partner_id": self.partners[0].id,
                "state": "draft",
            }
        )
        self.activity_auto._compute_consent_count()
        self.assertEqual(
            self.activity_auto.consent_count,
            1,
            "Consent count should be 1 after adding a consent.",
        )

    def test_compute_privacy_consent_count(self):
        """Test that privacy_consent_count is correctly updated."""
        self.assertEqual(
            self.partners[0].privacy_consent_count,
            0,
            "Initial privacy consent count should be 0.",
        )
        self.env["privacy.consent"].create(
            {
                "activity_id": self.activity_auto.id,
                "partner_id": self.partners[0].id,
                "state": "draft",
            }
        )
        self.partners[0]._compute_privacy_consent_count()

        self.assertEqual(
            self.partners[0].privacy_consent_count,
            1,
            "Privacy consent count should be 1 after adding a consent.",
        )


@odoo.tests.tagged("post_install", "-at_install")
class ActivitySecurity(ActivityCase):
    @classmethod
    def setUpClass(cls):
        """Create users based on privacy groups to tests ACLs"""
        cls._super_send = requests.Session.send
        super().setUpClass()

        # users
        cls.user_admin = cls.env.ref("base.user_admin")
        cls.user_privacy_user = mail_new_test_user(
            cls.env,
            groups="base.group_user,privacy.group_data_protection_user",
            login="user_privacy_user",
        )
        cls.user_privacy_manager = mail_new_test_user(
            cls.env,
            groups="base.group_user,privacy.group_data_protection_manager",
            login="user_privacy_manager",
        )

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        return cls._super_send(s, r, **kw)

    @users("user_privacy_user")
    def test_consent_acl_user(self):
        """Users can read"""
        activity_manual = self.activity_manual.with_user(self.env.user)
        activity_manual.read(["name"])

        # can't create consents
        with self.assertRaises(AccessError):
            activity_manual.action_new_consents()

    @users("user_privacy_manager")
    def test_consent_acl_manager(self):
        """Managers have all rights"""
        activity_manual = self.activity_manual.with_user(self.env.user)
        activity_manual.read(["name"])

        result = activity_manual.action_new_consents()
        consents = self.env[result["res_model"]].search(result["domain"], limit=1)
        consents.read(["state"])
        consents.unlink()

    def test_consent_controller_security_noaccess(self):
        """Test no access granted scenarios, should raise a NotFound and no
        crash / error"""
        result = self.activity_manual.action_new_consents()
        consent = self.env[result["res_model"]].search(result["domain"], limit=1)

        for res_id, token in [
            (-1, consent._token()),
            (-1, ""),
            (consent.id, ""),
        ]:
            response = self.url_open(f"/privacy/consent/accept/{res_id}/{token}")
            self.assertEqual(response.status_code, 404)
