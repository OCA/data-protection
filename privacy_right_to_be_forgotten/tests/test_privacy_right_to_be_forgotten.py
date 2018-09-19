# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.tests.common import SingleTransactionCase
from ..wizards.res_partner_gdpr import FIELDS_GDPR

CLEANUP_STRING = '*** GDPR removed ***'


class TestPrivacyGdpr(SingleTransactionCase):

    at_install = False
    post_install = True

    def test_privacy_gdpr(self):
        res_partner_gdpr = self.env['res.partner.gdpr']
        customer = self._create_test_customer()
        self._gdpr_cleanup(customer)
        for field in FIELDS_GDPR:
            attr = getattr(customer, field)
            if attr:
                self.assertTrue(res_partner_gdpr._get_remove_text() in attr)

    def _create_test_customer(self):
        vals = {}
        for field in FIELDS_GDPR:
            if field == 'name':
                vals.update({field: 'Name'})
            else:
                vals.update({field: False})
        return self.env['res.partner'].create(vals)

    def _gdpr_cleanup(self, customer):
        wiz = self.env['res.partner.gdpr'].create({
            'partner_ids': [(6, False, customer.ids)]})
        self.assertTrue(wiz.fields, True)
        wiz.action_gdpr_res_partner_cleanup()
