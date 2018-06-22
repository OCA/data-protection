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
    'name': "IT IS GDPR Extension",

    'summary': """
        Extended Website Contact View to give Customer the option on how to be contacted.
        View for DPO to look up Customer Data.
        Newletter Double Opt-In and -Out extending the Odoo mass_mailing module.
        """,

    'description': """
        Extended Website Contact View to give Customer the option on how to be contacted.
        View for DPO to look up Customer Data.
        Newletter Double Opt-In and -Out extending the Odoo mass_mailing module.
    """,

    'author': "IT IS AG",
    'website': "http://www.itis-odoo.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'version': '0.1',
    'category': 'Website',
    'depends': ['base',
                'website',
                'mass_mailing',
                'contacts',
                'website_crm',
                ],

    'data': [
        'views/contact_view.xml',
        'security/gdpr_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/contact_report.xml',
    ],
    'icon': "/itis_gdpr_extension/static/src/img/itisag.png",

}