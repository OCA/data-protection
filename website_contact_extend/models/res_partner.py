# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResContacts(models.Model):
    _inherit = "res.partner"

    contact_type = fields.Selection([
        ('no_contact', 'I do not want to be contacted.'),
        ('email_contact', 'I only want to be contacted by Email.'),
        ('phone_contact', 'I only want to be contacted by Phone.'),
        ('email_phone_contact', 'You can contact me by Email or Phone.')
    ],
        string='Contact Type',
        default='email_contact',
        help="Which way user want to be contacted.")
    letter_contact = fields.Boolean("Letter Contact")
    phone_contact = fields.Boolean("Phone Contact")
    email_contact = fields.Boolean("Email Contact")
    is_verified = fields.Boolean("Verified Email")
    last_updated = fields.Datetime("Letzte Aktualisierung")


class CrmLead(models.Model):
    _inherit = "crm.lead"

    email_link = fields.Char("Email verification link")
