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
        print(kwargs)

        if kwargs:

            contact_url = '%s/contact_by/%s' % (
                request.env['ir.config_parameter'].
                sudo().get_param('web.base.url'),
                kwargs.get("data"))

            link_data = base64.b64decode(kwargs.get("data")).decode("utf-8")\
                .split("####")
            email = link_data[0]
            contact_name = link_data[1]
            email_name = link_data[2]
            phone_name = link_data[3]
            letter_name = link_data[4]
            personal_data = link_data[5]
            request_gdpdr = link_data[6]
            crm_id = link_data[7]
            link_date = link_data[8]
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
            if not partner:
                partner = request.env['res.partner'].sudo().create(
                    {'name': contact_name, 'email': email})
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

                page_render_html = "<center style='color:green'>"\
                    "Thank You! Your email address has been verified!"\
                    "</center>"

                # print(request_gdpdr)
                if request_gdpdr == "True":
                    # print("Hit")
                    page_render_html = page_render_html + "<br/>"\
                        "<div style='text-align: center'>Click <a href='" + contact_url + \
                        "'>here</a> to choose how you want to be contacted</div>"

                if personal_data == "True":

                    request.env.ref(
                        'website_contact_extend.email_template_information_request'
                    ).sudo().send_mail(int(crm_id))

                    request.env.ref(
                        'website_contact_extend.requested_info_email_template'
                    ).sudo().send_mail(int(crm_id))

                return page_render_html

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
        request.session['review_form'] = ""
        request.session['form_data'] = ""
        request.session['form_data_dict'] = ""
        # request.clear_caches()

        if not model_record:
            return json.dumps(False)
        # need_send_email = False
        try:
            data = self.extract_data(model_record, request.params)
            print(data)
            # contact_type = False
            phone_contact = False
            letter_contact = False
            email_contact = False
            send_mail = False
            request_gdpdr = False

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
                if field_name == "send_mail" \
                        and field_value == "send_mail":
                    send_mail = True
                index += 1
            # contact_name = data.get("record").get("contact_name")
            # email_from = data.get("record").get("email_from")

        # If we encounter an issue while extracting data
        except ValidationError as e:
            # I couldn't find a cleaner way to pass data to an exception
            return json.dumps({'error_fields': e.args[0]})

        res_partner_data = data['record']

        try:
            contact_name = data.get("record").get("contact_name")
            email = data.get("record").get("email_from")
            company = data.get("record").get("partner_name")
            res_part_rec = request.env['res.partner'].sudo().search([
                ('email', '=', email),
                ('company_name', '=', company)])
            # ('name', '=', contact_name)])

            # ('company_name', '=', company)
            res_part_email = request.env['res.partner'].sudo().search([
                ('email', '=', email)])

            if len(res_part_rec) > 0 or len(res_part_rec) == 0 and len(res_part_email) > 0:
                request.session['review_form'] = "/contact-us-form-review"
                print('Display review')

                for chkbx_val_out in data['custom'].split('\n'):
                    if chkbx_val_out != '':
                        for chkbx_val_in in chkbx_val_out.split(':'):
                            print(chkbx_val_in)
                            if chkbx_val_in.strip() == "request_gdpdr":
                                request_gdpdr = True
                                break

                id_record = res_part_email[0].id

                rec_form = data.get('record')
                print(rec_form)
                # if 'phone' not in data.get('record'):
                #     rec_form['phone'] = ""
                lst_form_rec = []
                lst_form_rec.append(rec_form['email_from'])
                lst_form_rec.append(rec_form['name'])
                lst_form_rec.append(rec_form['partner_name'])
                lst_form_rec.append(rec_form['medium_id'])
                lst_form_rec.append(rec_form['contact_name'])
                lst_form_rec.append(rec_form['team_id'])
                lst_form_rec.append(rec_form['description'])
                lst_form_rec.append(rec_form['user_id'])
                lst_form_rec.append(request_gdpdr)
                lst_form_rec.append(send_mail)

                rec_form['send_mail'] = send_mail
                rec_form['request_gdpdr'] = request_gdpdr
                if 'phone' in rec_form:
                    lst_form_rec.append(rec_form['phone'])
                else:
                    lst_form_rec.append('')

                request.session['form_data'] = lst_form_rec
                request.session['form_data_dict'] = rec_form
                print(request.session['form_data'])

            # Some fields have additional SQL constraints
            #  that we can't check generically
            # Ex: crm.lead.probability which is a float between 0 and 1
            # TODO: How to get the name of the erroneous field ?
            else:
                #         code for adding new customer
                print('Hello')
                request.session['review_form'] = "/contactus-thank-you"

                res_cat = request.env['res.partner.category'].search(
                    [('name', '=', 'New')])
                print(res_cat)
                cat_id = 0

                if len(res_cat) == 0:
                    print('Hit')
                    id_part_res_cat = self.insert_record(
                        request,
                        request.env['ir.model'].search(
                            [('model', '=', 'res.partner.category')]),
                        {'name': 'New', 'create_uid': request.env.uid},
                        '',
                        ''
                    )
                    cat_id = id_part_res_cat
                    print(id_part_res_cat)
                else:
                    cat_id = res_cat[0].id

                res_partner_dict = {}

                # if 'phone' not in res_partner_data:
                #     res_partner_data['phone'] = ""

                res_partner_dict['name'] = res_partner_data['contact_name']
                res_partner_dict['display_name'] = res_partner_data['contact_name']
                res_partner_dict['email'] = res_partner_data['email_from']
                if 'phone' in res_partner_data:
                    res_partner_dict['phone'] = res_partner_data['phone']
                res_partner_dict['company_name'] = res_partner_data['partner_name']
                res_partner_dict['category_id'] = [[6, False, [cat_id]]]

                res_partner_company_dict = res_partner_dict.copy()
                res_partner_company_dict.pop('email')
                res_partner_company_dict.pop('company_name')
                if 'phone' in res_partner_company_dict:
                    res_partner_company_dict.pop('phone')

                res_partner_company_dict['name'] = res_partner_data['partner_name']
                res_partner_company_dict['display_name'] = res_partner_data['partner_name']
                res_partner_company_dict['customer'] = False
                res_partner_company_dict['is_company'] = True
                res_partner_company_dict['company_type'] = 'company'

                id_record_res_company = self.insert_record(
                    request,
                    request.env['ir.model'].search(
                        [('model', '=', 'res.partner')]),
                    res_partner_company_dict,
                    '',
                    data.get('meta')
                )

                res_partner_dict['parent_id'] = id_record_res_company

                id_record_res = self.insert_record(
                    request,
                    request.env['ir.model'].search(
                        [('model', '=', 'res.partner')]),
                    res_partner_dict,
                    '',
                    data.get('meta')
                )

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

                for chkbx_val_out in data['custom'].split('\n'):
                    if chkbx_val_out != '':
                        for chkbx_val_in in chkbx_val_out.split(':'):
                            print(chkbx_val_in)
                            if chkbx_val_in.strip() == "request_gdpdr":
                                request_gdpdr = True
                                break

                print("RGPDR" + str(request_gdpdr))
                # if request_gdpdr == True:

                if request_gdpdr == True or send_mail == True:
                    if id_record and model_name == "crm.lead":
                        crm_lead_obj = request.env['crm.lead'].sudo().search([
                            ('id', '=', id_record)]
                        )
                        email_data = crm_lead_obj.email_from + "####" + \
                            crm_lead_obj.contact_name + "####" + \
                            str(email_contact) + "####" + \
                            str(phone_contact) + "####" + \
                            str(letter_contact) + "####" + \
                            str(send_mail) + "####" + \
                            str(request_gdpdr) + "####" + \
                            str(id_record) + "####" + \
                            str(crm_lead_obj.create_date)

                        print(email_data)
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
                        ).sudo().send_mail(id_record)

        except IntegrityError:
            return json.dumps(False)

        print(request.session['review_form'])
        request.session['form_builder_model_model'] = model_record.model
        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id'] = id_record

        return json.dumps({'id': id_record})
