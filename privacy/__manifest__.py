# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    'name': 'Data Privacy and Protection',
    'version': '10.0.1.0.0',
    'category': 'Data Protection',
    'summary': 'Provides data privacy and protection features '
               'to comply to regulations, such as GDPR.',
    'author': "Eficent, "
              "Odoo Community Association (OCA)",
    'website': 'http://www.github.com/OCA/data-protection',
    'license': 'AGPL-3',
    'data': [
        'security/data_protection.xml',
        'views/data_protection_menu_view.xml',
    ],
    'installable': True,
    'application': True,
}
