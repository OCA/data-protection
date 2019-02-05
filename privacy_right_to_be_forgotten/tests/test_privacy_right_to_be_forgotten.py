# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from .common import TestPrivacyGdpr
from ..wizards.res_partner_gdpr import FIELDS_GDPR


class TestPrivacyGdprPartner(TestPrivacyGdpr):

    at_install = False
    post_install = True

    def test_privacy_gdpr(self):
        res_partner_gdpr = self.env['res.partner.gdpr']
        customer = self._create_test_customer()
        self._gdpr_cleanup(customer)
        for field in FIELDS_GDPR:
            attr = getattr(customer, field)
            if attr and isinstance(attr, basestring):
                self.assertTrue(res_partner_gdpr._get_remove_text() in attr)

    def test_child_removal(self):
        res_partner_gdpr = self.env['res.partner.gdpr']
        customer = self._create_test_customer()
        child = self.env['res.partner'].create({
            'parent_id': customer.id,
            'name': 'Child Partner'})
        self._gdpr_cleanup(customer)
        self.assertTrue(res_partner_gdpr._get_remove_text() in child.name)
