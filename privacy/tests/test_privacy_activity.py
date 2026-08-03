# Copyright 2026 Rapsodoo Italia S.r.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestPrivacyActivity(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Activity = cls.env["privacy.activity"]
        cls.dp_user = new_test_user(
            cls.env,
            login="privacy_dp_user",
            groups="privacy.group_data_protection_user",
        )
        cls.dp_manager = new_test_user(
            cls.env,
            login="privacy_dp_manager",
            groups="privacy.group_data_protection_manager",
        )

    # ------------------------------------------------------------------
    # field defaults
    # ------------------------------------------------------------------
    def test_default_controller_id(self):
        activity = self.Activity.create({"name": "Activity 1"})
        self.assertEqual(activity.controller_id, self.env.user.company_id.partner_id)

    def test_explicit_controller_id_is_kept(self):
        partner = self.env["res.partner"].create({"name": "Explicit Controller"})
        activity = self.Activity.create(
            {"name": "Activity 2", "controller_id": partner.id}
        )
        self.assertEqual(activity.controller_id, partner)

    def test_active_defaults_to_true(self):
        activity = self.Activity.create({"name": "Activity 3"})
        self.assertTrue(activity.active)

    def test_archive_hides_from_default_search(self):
        activity = self.Activity.create({"name": "Activity 4"})
        activity.active = False
        self.assertNotIn(activity, self.Activity.search([]))
        self.assertIn(
            activity, self.Activity.with_context(active_test=False).search([])
        )

    # ------------------------------------------------------------------
    # security: group_data_protection_user is read-only
    # ------------------------------------------------------------------
    def test_data_protection_user_can_read(self):
        activity = self.Activity.create({"name": "Activity 5"})
        activity.with_user(self.dp_user).read(["name"])

    def test_data_protection_user_cannot_write(self):
        activity = self.Activity.create({"name": "Activity 6"})
        with self.assertRaises(AccessError):
            activity.with_user(self.dp_user).write({"name": "Renamed"})

    def test_data_protection_user_cannot_create(self):
        with self.assertRaises(AccessError):
            self.Activity.with_user(self.dp_user).create({"name": "Activity 7"})

    def test_data_protection_user_cannot_unlink(self):
        activity = self.Activity.create({"name": "Activity 8"})
        with self.assertRaises(AccessError):
            activity.with_user(self.dp_user).unlink()

    # ------------------------------------------------------------------
    # security: group_data_protection_manager has full access
    # ------------------------------------------------------------------
    def test_data_protection_manager_can_create(self):
        activity = self.Activity.with_user(self.dp_manager).create(
            {"name": "Activity 9"}
        )
        self.assertTrue(activity)

    def test_data_protection_manager_can_write(self):
        activity = self.Activity.create({"name": "Activity 10"})
        activity.with_user(self.dp_manager).write({"name": "Renamed"})
        self.assertEqual(activity.name, "Renamed")

    def test_data_protection_manager_can_unlink(self):
        activity = self.Activity.create({"name": "Activity 11"})
        activity.with_user(self.dp_manager).unlink()
        self.assertFalse(activity.exists())

    # ------------------------------------------------------------------
    # security groups wiring (res.groups.privilege replacing category_id)
    # ------------------------------------------------------------------
    def test_groups_share_data_protection_privilege(self):
        privilege = self.env.ref("privacy.privilege_data_protection")
        self.assertEqual(
            self.env.ref("privacy.group_data_protection_user").privilege_id,
            privilege,
        )
        self.assertEqual(
            self.env.ref("privacy.group_data_protection_manager").privilege_id,
            privilege,
        )

    def test_manager_group_implies_user_group(self):
        user_group = self.env.ref("privacy.group_data_protection_user")
        manager_group = self.env.ref("privacy.group_data_protection_manager")
        self.assertIn(user_group, manager_group.implied_ids)
