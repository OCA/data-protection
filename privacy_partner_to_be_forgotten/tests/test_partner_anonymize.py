# Copyright (C) 2025 Cetmix OÜ
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import re

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPartnerAnonymize(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test company
        cls.partner_company = cls.env["res.partner"].create(
            {
                "name": "Sodasopa",
                "is_company": True,
                "phone": "+1 123-456-7890",
                "email": "info@sodasopa.com",
                "street": "123 Main St",
                "city": "South Park",
                "zip": "80435",
                "country_id": cls.env.ref("base.us").id,
                "website": "www.sodasopa.com",
                "vat": "US123456789",
            }
        )

        # Create test partners
        cls.partner_eric = cls.env["res.partner"].create(
            {
                "name": "Eric Cartman",
                "parent_id": cls.partner_company.id,
                "phone": "+1 123-456-7891",
                "mobile": "+1 123-456-7892",
                "email": "eric@sodasopa.com",
                "street": "124 Main St",
                "city": "South Park",
                "zip": "80435",
                "country_id": cls.env.ref("base.us").id,
                "function": "Manager",
            }
        )

        cls.partner_butters = cls.env["res.partner"].create(
            {
                "name": "Butters Stotch",
                "parent_id": cls.partner_company.id,
                "phone": "+1 123-456-7893",
                "mobile": "+1 123-456-7894",
                "email": "butters@sodasopa.com",
                "street": "125 Main St",
                "city": "South Park",
                "zip": "80435",
                "country_id": cls.env.ref("base.us").id,
                "function": "Assistant",
            }
        )

        cls.partner_kenny = cls.env["res.partner"].create(
            {
                "name": "Kenny McCormick",
                "parent_id": cls.partner_eric.id,
                "phone": "+1 123-456-7895",
                "mobile": "+1 123-456-7896",
                "email": "kenny@sodasopa.com",
                "street": "126 Main St",
                "city": "South Park",
                "zip": "80435",
                "country_id": cls.env.ref("base.us").id,
                "function": "Intern",
            }
        )

        cls.partner_stanley = cls.env["res.partner"].create(
            {
                "name": "Stanley Marsh",
                "phone": "+1 123-456-7897",
                "mobile": "+1 123-456-7898",
                "email": "stan@sp.com",
                "street": "127 Main St",
                "city": "South Park",
                "zip": "80435",
                "country_id": cls.env.ref("base.us").id,
                "function": "Student",
            }
        )

        # Create test users
        cls.user_company = cls.env["res.users"].create(
            {
                "partner_id": cls.partner_company.id,
                "login": "test_sodasopa",
                "password": "sodasopa",
                "name": "Sodasopa",
                "email": "info@sodasopa.com",
                "groups_id": [(4, cls.env.ref("base.group_user").id)],
            }
        )

        cls.user_eric = cls.env["res.users"].create(
            {
                "partner_id": cls.partner_eric.id,
                "login": "test_eric",
                "password": "eric",
                "name": "Eric Cartman",
                "email": "eric@sodasopa.com",
                "groups_id": [(4, cls.env.ref("base.group_user").id)],
            }
        )

        cls.user_butters = cls.env["res.users"].create(
            {
                "partner_id": cls.partner_butters.id,
                "login": "test_butters",
                "password": "butters",
                "name": "Butters Stotch",
                "email": "butters@sodasopa.com",
                "groups_id": [(4, cls.env.ref("base.group_user").id)],
            }
        )

        cls.user_kenny = cls.env["res.users"].create(
            {
                "partner_id": cls.partner_kenny.id,
                "login": "test_kenny",
                "password": "kenny",
                "name": "Kenny McCormick",
                "email": "kenny@sodasopa.com",
                "groups_id": [(4, cls.env.ref("base.group_user").id)],
            }
        )

        cls.user_stanley = cls.env["res.users"].create(
            {
                "partner_id": cls.partner_stanley.id,
                "login": "test_stan",
                "password": "stan",
                "name": "Stanley Marsh",
                "email": "stan@sp.com",
                "groups_id": [(4, cls.env.ref("base.group_user").id)],
            }
        )

        cls.test_user = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "email": "test_user@example.com",
                "groups_id": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("base.group_system").id),
                    (4, cls.env.ref("base.group_partner_manager").id),
                    (
                        4,
                        cls.env.ref(
                            "privacy_partner_to_be_forgotten.group_partner_anonymize"
                        ).id,
                    ),
                ],
            }
        )

        cls.test_user_no_rights = cls.env["res.users"].create(
            {
                "name": "Test User No Rights",
                "login": "test_user_no_rights",
                "email": "test_user_no_rights@example.com",
                "groups_id": [(4, cls.env.ref("base.group_user").id)],
            }
        )

        cls.env["ir.model.access"].create(
            {
                "name": "access_res_partner_full",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "perm_read": True,
                "perm_write": True,
                "perm_create": True,
                "perm_unlink": True,
                "group_id": cls.env.ref(
                    "privacy_partner_to_be_forgotten.group_partner_anonymize"
                ).id,
            }
        )

        cls.message = cls.env["mail.message"].create(
            {
                "model": "res.partner",
                "res_id": cls.partner_eric.id,
                "body": "Test message",
                "message_type": "comment",
            }
        )

        cls.attachment = cls.env["ir.attachment"].create(
            {
                "name": "Test Attachment",
                "res_model": "res.partner",
                "res_id": cls.partner_eric.id,
                "datas": (
                    "R0lGODlhAQABAIAAAP///wAAACwAAAAAAQABAAACAkQBADs="  # Minimal GIF
                ),
            }
        )

    def _create_anonymize_wizard(self, partner_ids, user):
        """Helper method to create and return an anonymization wizard"""
        with Form(
            self.env["partner.anonymize.wizard"]
            .with_user(user)
            .with_context(default_partner_ids=partner_ids, active_ids=partner_ids)
        ) as wizard:
            wizard_id = wizard.save()

        return wizard_id

    def _check_anonymized_partner(self, partner, original_name):
        """Helper method to check if a partner is properly anonymized"""
        # Check name format (initials + "Anonymized")
        initials = "".join(part[0].upper() for part in original_name.split() if part)
        self.assertEqual(partner.name, f"{initials} Anonymized")

        # Check email format
        email_pattern = rf"^{initials.lower()}_[\d\.]{{8}}_\d+@anonymized\.oca$"
        self.assertTrue(re.match(email_pattern, partner.email))

        self.assertFalse(partner.phone)
        self.assertFalse(partner.mobile)
        self.assertFalse(partner.street)
        self.assertFalse(partner.street2)
        self.assertFalse(partner.city)
        self.assertFalse(partner.state_id)
        self.assertFalse(partner.zip)
        self.assertFalse(partner.country_id)
        self.assertFalse(partner.function)
        self.assertFalse(partner.title)
        self.assertFalse(partner.vat)
        self.assertFalse(partner.ref)
        self.assertFalse(partner.comment)
        self.assertFalse(partner.website)
        self.assertFalse(partner.image_1920)
        self.assertFalse(partner.active)

        return True

    def _check_anonymized_user(self, user, partner):
        """Helper method to check if a user is properly anonymized"""
        self.assertEqual(user.login, partner.email)
        self.assertEqual(user.email, partner.email)
        self.assertFalse(user.active)
        self.assertIn("Anonymized", user.signature)

        return True

    def test_01_anonymize_individual_with_child(self):
        """Test Case 1: Anonymize Individual Contact (Parent with Child)"""
        eric_name = self.partner_eric.name
        butters_name = self.partner_butters.name

        # Set Butters as Eric's child
        self.partner_butters.write({"parent_id": self.partner_eric.id})

        # Verify initial state
        self.assertEqual(self.partner_butters.parent_id, self.partner_eric)

        # Anonymize Eric (parent)
        wizard = self._create_anonymize_wizard([self.partner_eric.id], self.test_user)
        wizard.action_confirm()

        # Check Eric's anonymization
        self._check_anonymized_partner(self.partner_eric, eric_name)
        self._check_anonymized_user(self.user_eric, self.partner_eric)

        # Check Butters' anonymization (child)
        self._check_anonymized_partner(self.partner_butters, butters_name)
        self._check_anonymized_user(self.user_butters, self.partner_butters)

        # Check messages and attachments
        for partner in [self.partner_eric, self.partner_butters]:
            # Check messages (should only have anonymization log)
            messages = self.env["mail.message"].search(
                [
                    ("model", "=", "res.partner"),
                    ("res_id", "=", partner.id),
                ]
            )
            self.assertEqual(len(messages), 1)
            self.assertIn("anonymized", messages[0].body)

            # Check attachments (should be empty)
            attachments = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "res.partner"),
                    ("res_id", "=", partner.id),
                ]
            )
            self.assertEqual(len(attachments), 0)

    def test_02_anonymize_child_record_only(self):
        """Test Case 2: Anonymize Child Record Only"""

        eric_name = self.partner_eric.name
        butters_name = self.partner_butters.name

        # Set Butters as Eric's child
        self.partner_butters.write({"parent_id": self.partner_eric.id})

        # Verify initial state
        self.assertEqual(self.partner_butters.parent_id, self.partner_eric)

        # Anonymize Butters only
        wizard = self._create_anonymize_wizard(
            [self.partner_butters.id], self.test_user
        )
        wizard.action_confirm()

        # Check that Butters (child) is anonymized
        self._check_anonymized_partner(self.partner_butters, butters_name)
        self._check_anonymized_user(self.user_butters, self.partner_butters)

        # Check that Eric (parent) is not anonymized
        self.assertEqual(self.partner_eric.name, eric_name)
        self.assertTrue(self.partner_eric.active)

        # Check messages and attachments for Butters
        messages = self.env["mail.message"].search(
            [
                ("model", "=", "res.partner"),
                ("res_id", "=", self.partner_butters.id),
            ]
        )
        self.assertEqual(len(messages), 1)  # Only anonymization log should remain
        self.assertIn("anonymized", messages[0].body)

        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", self.partner_butters.id),
            ]
        )
        self.assertEqual(len(attachments), 0)

    def test_03_anonymize_company_not_allowed(self):
        """Test Case 3: Attempt to Anonymize Company (should fail)"""
        # Try to anonymize the company
        wizard = self._create_anonymize_wizard(
            [self.partner_company.id], self.test_user
        )

        # This should raise a UserError
        with self.assertRaises(UserError) as context:
            wizard.action_confirm()

        # Check the error message
        self.assertIn(
            "Cannot anonymize the following company records", str(context.exception)
        )
        self.assertIn(self.partner_company.name, str(context.exception))

        # Verify the company is not anonymized
        self.assertTrue(self.partner_company.active)
        self.assertNotIn("Anonymized", self.partner_company.name)

    def test_04_anonymize_one_child_record(self):
        """Test Case 4: Anonymize One of the Child Records"""
        # Store original names for later comparison
        company_name = self.partner_company.name
        eric_name = self.partner_eric.name
        butters_name = self.partner_butters.name

        # Set both Eric and Butters as children of the company
        self.partner_eric.write({"parent_id": self.partner_company.id})
        self.partner_butters.write({"parent_id": self.partner_company.id})

        # Verify initial state
        self.assertEqual(self.partner_eric.parent_id, self.partner_company)
        self.assertEqual(self.partner_butters.parent_id, self.partner_company)

        # Anonymize Butters only
        wizard = self._create_anonymize_wizard(
            [self.partner_butters.id], self.test_user
        )
        wizard.action_confirm()

        # Check that Butters is anonymized
        self._check_anonymized_partner(self.partner_butters, butters_name)
        self._check_anonymized_user(self.user_butters, self.partner_butters)

        # Check that Eric and Company remain unchanged
        self.assertEqual(self.partner_eric.name, eric_name)
        self.assertTrue(self.partner_eric.active)
        self.assertEqual(self.partner_company.name, company_name)
        self.assertTrue(self.partner_company.active)

        # Check messages and attachments for Butters
        messages = self.env["mail.message"].search(
            [
                ("model", "=", "res.partner"),
                ("res_id", "=", self.partner_butters.id),
            ]
        )
        self.assertEqual(len(messages), 1)  # Only anonymization log should remain
        self.assertIn("anonymized", messages[0].body)

        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", self.partner_butters.id),
            ]
        )
        self.assertEqual(len(attachments), 0)

    def test_05_anonymize_deeply_nested_child(self):
        """Test Case 5: Anonymize Deeply Nested Child Record"""
        # Store original names for later comparison
        company_name = self.partner_company.name
        eric_name = self.partner_eric.name
        butters_name = self.partner_butters.name
        stanley_name = self.partner_stanley.name

        # Set up the hierarchy:
        self.partner_eric.write({"parent_id": self.partner_company.id})
        self.partner_butters.write({"parent_id": self.partner_company.id})
        self.partner_stanley.write({"parent_id": self.partner_eric.id})

        # Verify initial state
        self.assertEqual(self.partner_stanley.parent_id, self.partner_eric)
        self.assertEqual(self.partner_eric.parent_id, self.partner_company)
        self.assertEqual(self.partner_butters.parent_id, self.partner_company)

        # Verify Stanley's initial state
        self.assertEqual(self.partner_stanley.name, stanley_name)
        self.assertNotIn("Anonymized", stanley_name)

        # Anonymize Stanley (deeply nested child)
        wizard = self._create_anonymize_wizard(
            [self.partner_stanley.id], self.test_user
        )
        wizard.action_confirm()

        # Check that Stanley is anonymized
        self._check_anonymized_partner(self.partner_stanley, stanley_name)
        self._check_anonymized_user(self.user_stanley, self.partner_stanley)

        # Check that parent (Eric) remains unchanged
        self.assertEqual(self.partner_eric.name, eric_name)
        self.assertTrue(self.partner_eric.active)

        # Check that company and other child (Butters) remain unchanged
        self.assertEqual(self.partner_company.name, company_name)
        self.assertTrue(self.partner_company.active)
        self.assertEqual(self.partner_butters.name, butters_name)
        self.assertTrue(self.partner_butters.active)

        # Check messages and attachments for Stanley
        messages = self.env["mail.message"].search(
            [
                ("model", "=", "res.partner"),
                ("res_id", "=", self.partner_stanley.id),
            ]
        )
        self.assertEqual(len(messages), 1)  # Only anonymization log should remain
        self.assertIn("anonymized", messages[0].body)

        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "res.partner"),
                ("res_id", "=", self.partner_stanley.id),
            ]
        )
        self.assertEqual(len(attachments), 0)

    def test_06_anonymize_multiple_partners(self):
        """Test anonymizing multiple partners at once"""
        # Store original names for later comparison
        eric_name = self.partner_eric.name
        butters_name = self.partner_butters.name

        # Anonymize both Eric and Butters
        wizard = self._create_anonymize_wizard(
            [self.partner_eric.id, self.partner_butters.id], self.test_user
        )
        wizard.action_confirm()

        # Check that both partners are anonymized
        self._check_anonymized_partner(self.partner_eric, eric_name)
        self._check_anonymized_user(self.user_eric, self.partner_eric)

        self._check_anonymized_partner(self.partner_butters, butters_name)
        self._check_anonymized_user(self.user_butters, self.partner_butters)

    def test_07_validate_access_rights(self):
        """Test validation of access rights in _validate_partners_for_anonymization"""
        # Create wizard with user that has anonymization rights
        wizard = self._create_anonymize_wizard(
            [self.partner_stanley.id], self.test_user
        )

        # Try to execute action_confirm with user that doesn't have rights
        wizard = wizard.with_user(self.test_user_no_rights)

        # This should raise an AccessError
        with self.assertRaises(AccessError) as context:
            wizard.action_confirm()

        # Check the error message
        self.assertIn(
            "You don't have permission to anonymize partners", str(context.exception)
        )

        # Verify the partner is not anonymized
        self.assertTrue(self.partner_stanley.active)
        self.assertNotIn("Anonymized", self.partner_stanley.name)
