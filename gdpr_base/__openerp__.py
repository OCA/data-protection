# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    'name': 'GDPR Base',
    'version': '9.0.1.0.0',
    'category': 'GDPR',
    'summary': 'Provides a shared base for all GDPR modules.',
    'author': "Eficent, "
              "Odoo Community Association (OCA)",
    'website': 'http://www.github.com/Eficent/gdpr,',
    'license': 'AGPL-3',
    'depends': ['data_protection_base'],
    'data': [
        'views/gdpr_menu_view.xml',
    ],
    'installable': True,
}
