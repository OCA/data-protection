#####################################################################
#
#    IT IS AG, software solutions: http://www.itis.de
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#
#####################################################################

{
    'name': 'Contact Search Form',

    'summary': "Multiple models can be searched for specified string by DPO",

    'author': 'IT IS AG, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/data-protection',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/
    # openerp/addons/base/module/module_data.xml
    # for the full list
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Contacts',
    'depends': ['base',
                'contacts',
                ],

    'data': [
        'security/gdpr_security.xml',
        'security/ir.model.access.csv',
        'views/contact_search.xml',
    ],

}
