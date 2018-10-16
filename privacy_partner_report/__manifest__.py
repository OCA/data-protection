# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    'name': 'Privacy Partner Report',
    'version': '10.0.1.0.0',
    'category': 'GDPR',
    'summary': 'Show the transactions that a specific partner is involved in.',
    'author': "Eficent, "
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/data-protection/',
    'license': 'AGPL-3',
    'depends': ['privacy', 'report_xlsx'],
    'data': [
        'wizard/privacy_report_partner_wizard.xml',
        'views/privacy_report.xml',
        'views/privacy_menu_view.xml',
    ],
    'installable': True,
    'maintainers': ['mreficent'],
}
