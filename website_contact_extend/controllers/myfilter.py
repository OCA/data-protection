# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.website_form.controllers import main as parent_controller
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
import base64
import json


class VerifyController(http.Controller):
    @http.route('/verify_email',
                type='http',
                auth="public",
                methods=['GET'],
                website=True)
    def verify_email(self, **kwargs):
        if kwargs:
            link_data = base64.b64decode(kwargs.get("data")).decode("utf-8")\
                .split("####")
            email = link_data[0]
            contact_name = link_data[1]
            email_name = link_data[2]
            phone_name = link_data[3]
            letter_name = link_data[4]
            link_date = link_data[5]
            link_date = link_date.split(" ")[0].replace("-", "")
            import datetime
            today = datetime.date.today()
            link = datetime.datetime.strptime(link_date, "%Y%m%d").date()
            diff = today - link
            if diff.days > 5 or diff.days < 0:
                return "<center style='color:red'>Not valid!<br/>"\
                       "The link you entered is either not valid or expired."\
                       "<br/>Please request a new link.</center>"
            partner = request.env['res.partner'].sudo().search([
                ('email', '=', email),
                ('name', '=', contact_name)
            ])
            if partner:
                for part in partner:
                    part.is_verified = True
                    part.last_updated = part.write_date
                    if email_name == "True":
                        part.email_contact = True
                    else:
                        part.email_contact = False
                    if phone_name == "True":
                        part.phone_contact = True
                    else:
                        part.phone_contact = False
                    if letter_name == "True":
                        part.letter_contact = True
                    else:
                        part.letter_contact = False
                    request.env.ref(
                        'website_contact_extend.confirmation_email_template'
                    ).sudo().send_mail(part.id)
                return "<center style='color:green'>"\
                       "Thank You! Your email address has been verified!"\
                       "</center>"
            else:
                return "<center style='color:red'>Not valid!<br/>"\
                       "The link you entered is either not valid or expired."\
                       "<br/>Please request a new link.</center>"


class MyFilter(parent_controller.WebsiteForm):

    @http.route('/website_form/<string:model_name>',
                type='http',
                auth="public",
                methods=['POST'],
                website=True)
    def website_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].sudo().search([
            ('model', '=', model_name),
            ('website_form_access', '=', True)
        ])
        if not model_record:
            return json.dumps(False)
        # need_send_email = False
        try:
            data = self.extract_data(model_record, request.params)
            # contact_type = False
            phone_contact = False
            letter_contact = False
            email_contact = False
            send_mail = True
            index = 0
            for field_name, field_value in request.params.items():
                # if field_name == "contact_type":
                    # contact_type = field_value
                if field_name == "send_mail" and field_value == "send_mail":
                    send_mail = True
                if field_name == "phone_contact" \
                        and field_value == "phone_contact":
                    phone_contact = True
                if field_name == "letter_contact" \
                        and field_value == "letter_contact":
                    letter_contact = True
                if field_name == "email_contact" \
                        and field_value == "email_contact":
                    email_contact = True
                index += 1
            # contact_name = data.get("record").get("contact_name")
            # email_from = data.get("record").get("email_from")

        # If we encounter an issue while extracting data
        except ValidationError as e:
            # I couldn't find a cleaner way to pass data to an exception
            return json.dumps({'error_fields': e.args[0]})

        try:
            id_record = self.insert_record(
                request,
                model_record,
                data['record'],
                data['custom'],
                data.get('meta')
            )
            if id_record:
                self.insert_attachment(
                    model_record,
                    id_record,
                    data['attachments']
                )
            if id_record and send_mail and model_name == "crm.lead":
                crm_lead_obj = request.env['crm.lead'].sudo().search([
                    ('id', '=', id_record)]
                )
                email_data = crm_lead_obj.email_from + "####" +\
                    crm_lead_obj.contact_name + "####" +\
                    str(email_contact) + "####" +\
                    str(phone_contact) + "####" +\
                    str(letter_contact)+"####" +\
                    str(crm_lead_obj.create_date)
                ency_email = base64.b64encode(email_data.encode()).decode(
                    "utf-8"
                )
                action_url = '%s/verify_email/?data=%s' % (
                    request.env['ir.config_parameter'].
                    sudo().get_param('web.base.url'),
                    ency_email,
                )
                if crm_lead_obj:
                    crm_lead_obj.email_link = action_url
                request.env.ref(
                    'website_contact_extend.verification_email_template'
                ).send_mail(id_record)
        # Some fields have additional SQL constraints
        #  that we can't check generically
        # Ex: crm.lead.probability which is a float between 0 and 1
        # TODO: How to get the name of the erroneous field ?
        except IntegrityError:
            return json.dumps(False)

        request.session['form_builder_model_model'] = model_record.model
        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id'] = id_record

        return json.dumps({'id': id_record})
