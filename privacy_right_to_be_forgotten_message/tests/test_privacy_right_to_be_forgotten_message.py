# -*- coding: utf-8 -*-
# Copyright 2019 Akretion <https://akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.addons.privacy_right_to_be_forgotten.tests.common import (
    TestPrivacyGdpr
)


class TestPrivacyGdprMessage(TestPrivacyGdpr):

    def test_privacy_gdpr_message(self):
        vals = {
            'name': 'Test',
        }
        partner = self.env['res.partner'].create(vals)
        # A message is created automatically on creation
        self.assertEqual(1, len(partner.message_ids))
        self._gdpr_cleanup(partner)
        self.assertEqual(0, len(partner.message_ids))
