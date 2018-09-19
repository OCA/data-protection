# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Privacy GDPR",
    "version": "8.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "GDPR",
    "summary": "Allow a user to delete personal information for a customer.",
    "depends": [
        'base',
    ],
    "data": [
        'views/res_partner_gdpr.xml',
        'data/ir_actions_act_window.xml',
    ],
    "installable": True,
    "application": False,
}
