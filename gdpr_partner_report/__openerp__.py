# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    'name': 'GDPR Partner Report',
    'version': '9.0.1.0.0',
    'category': 'GDPR',
    'summary': 'Show the transactions that a specific partner is involved in.',
    'author': "Eficent, "
              "Odoo Community Association (OCA)",
    'website': 'http://www.github.com/Eficent/gdpr,',
    'license': 'AGPL-3',
    'depends': ['gdpr_base', 'report_xlsx'],
    'data': [
        'wizard/gdpr_report_partner_wizard.xml',
        'views/gdpr_report.xml',
        'views/gdpr_menu_view.xml',
        'views/report_partner.xml',
    ],
    'installable': True,
}
