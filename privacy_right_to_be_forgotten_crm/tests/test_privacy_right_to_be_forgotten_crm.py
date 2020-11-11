# -*- coding: utf-8 -*-
# Copyright 2019 Akretion <https://akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.addons.privacy_right_to_be_forgotten.tests.common import (
    TestPrivacyGdpr
)


class TestPrivacyGdprCRM(TestPrivacyGdpr):

    def test_privacy_gdpr_crm(self):
        partner_gdpr = self.env['res.partner.gdpr']
        customer = self._create_test_customer()
        lead_vals = {
            'name': 'Partner Test Lead',
            'partner_id': customer.id,
            'street': 'test street',
            'email_from': 'test email'
        }
        lead = self.env['crm.lead'].create(lead_vals)
        self._gdpr_cleanup(customer)
        self.assertEqual(False, lead.active)
        self.assertTrue(partner_gdpr._get_remove_text() == lead.email_from)
