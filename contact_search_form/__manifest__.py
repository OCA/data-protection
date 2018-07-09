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
    'name': "Contact Search Form",

    'summary': """

        View for Data Protection Officer (DPO) to look up Customer Data. Odoo models can be searched for specified string.

        """,

    'description': """

        View for Data Protection Officer (DPO) to look up Customer Data. Odoo models can be searched for specified string.
        To access contact search in contacts view, user must activate 'Data Protection Officer' checkbox in Technical Settings.

    """,

    'author': "IT IS AG, Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/data-protection",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'version': '11.0.1.0.0',
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