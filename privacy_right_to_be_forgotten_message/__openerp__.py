# -*- coding: utf-8 -*-
# Copyright 2019 Akretion <https://akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Privacy GDPR Messages",
    "version": "8.0.1.0.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "GDPR",
    "summary": "Delete messages linked to a customer when erasing its datas",
    "depends": [
        'privacy_right_to_be_forgotten',
        'mail',
    ],
    "data": [
    ],
    "installable": True,
    "application": False,
    'auto_install': True,
}
