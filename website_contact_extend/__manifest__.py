# -*- coding: utf-8 -*-

##############################################################################
#
#    IT IS AG, software solutions
#    Copyright (C) 2015-TODAY IT IS AG (<http://www.itis.de, www.itis.us>).
#
#
#    The software works in conjunction with other software distributed from
#    other parties which is licensed under the GNU Lesser General Public
#    License (LGPL).
#    Those pieces are not owned by IT IS AG and therefore not under the terms
#    of the IT IS EULA, and WITHOUT ANY WARRANTY; without even the implied
#    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with IT IS Odoo Textblock. If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': "Website Contact Form Extend",

    'summary': """

        Extended Website Contact View to give Customer the option on how to be contacted.

        """,

    'description': """

        Extended Website Contact View to give Customer the option on how to be contacted.

        Customer can verifiy his email address with a verification link. Following that the mode of future contact can be chosen and
        a GDPR information request can be submitted.

    """,

    'author': "IT IS AG, Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/data-protection",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'version': '11.0.1.0.0',
    'category': 'Website',
    'depends': ['base',
                #'website',
                'contacts',
                'website_crm',
                ],

    'data': [
        'views/website_contact.xml',
        'views/res_partner.xml',
        'views/contact_report.xml',
        'data/email_templates.xml',
    ],

}