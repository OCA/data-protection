# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.website_form.controllers import main as parent_controller
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
import base64
import json

link_data = {}


class ContactByController(http.Controller):

    @http.route('/check_user_exists/', type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def check_user_exists(self, email_from, company_name, **kwargs):
        res_part_rec = request.env['res.partner'].sudo().search([
            ('email', '=', email_from),
            ('company_name', '=', company_name)])

        res_part_email = request.env['res.partner'].sudo().search([
            ('email', '=', email_from)])

        if len(res_part_rec) > 0 or len(res_part_rec) == 0 and len(res_part_email) > 0:
            # if partner:
            return True
        return False

    @http.route('/contact-us-form-review/',
                type='http',
                auth="public",
                methods=['GET'],
                website=True)
    def contact_us_form_review(self, **kwargs):
        # print(kwargs.get("data"))
        # link_data =base64.b64decode(kwargs.get("data")).decode("utf-8") \
        # print('FD')
        # print(request.session['form_data'])
        return http.request.render('website_contact_extend.review_form', {'form_data': request.session['form_data'],
                                                                          'form_data_dict': request.session['form_data_dict']})

    @http.route('/contact_by/<string:data>',
                type='http',
                auth="public",
                methods=['GET'],
                website=True)
    def contact_by(self, data, **kwargs):
        global link_data
        print(data)
        # print(kwargs.get("data"))
        # link_data =base64.b64decode(kwargs.get("data")).decode("utf-8") \
        link_data = data
        return http.request.render('website_contact_extend.contactby_form')
        # return "<center style='color:red'>You are at the right place</center>"

    @http.route('/contact_by_send/<string:model_name>',
                type='http',
                auth="public",
                methods=['POST'],
                website=True)
    def contact_by_send(self, model_name, **kwargs):
        global link_data
        # form_contact_name = ""

        model_record = request.env['ir.model'].sudo().search([
            ('model', '=', model_name),
            ('website_form_access', '=', True)
        ])

        print(model_record)
        print(request.params)
        means_of_cont_dict = request.params

        if 'letter_contact' in means_of_cont_dict:
            letter_name = "True"
        else:
            letter_name = "False"

        if 'email_contact' in means_of_cont_dict:
            email_name = "True"
        else:
            email_name = "False"

        if 'phone_contact' in means_of_cont_dict:
            phone_name = "True"
        else:
            phone_name = "False"

        if not model_record:
            return json.dumps(False)

        # print(link_data)
        link_data_split = base64.b64decode(
            link_data).decode("utf-8").split("####")
        # print(link_data_split)

        email = link_data_split[0]
        contact_name = link_data_split[1]

        print(email, contact_name, email_name, phone_name, letter_name)

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

        request.session['form_builder_model_model'] = model_record.model
        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id'] = partner[0].id

        return json.dumps({'id': partner[0].id})

        # return http.request.render('website_contact_extend.disp_msg_template', {'message_success': 'Means of contact changed!'})
        #     return "<p style='color: green'>Means of contact changed!</p>"
        # else:
        #     # return http.request.render('website_contact_extend.disp_msg_template', {'message_failure': 'Could not change your means of contact. Please request a new link'})
        #     return "<p style='color: red'>Could not change your means of contact. Please request a new link</p>"


class FormReview(parent_controller.WebsiteForm):

    @http.route('/form_review_send/<string:model_name>',
                type='http',
                auth="public",
                methods=['POST'],
                website=True)
    def form_review_send(self, model_name, **kwargs):
        # model_name = 'crm.lead'
        print('Send')

        res_partner_data = request.session['form_data_dict']
        model_record = request.env['ir.model'].sudo().search([
            ('model', '=', model_name),
            ('website_form_access', '=', True)
        ])

        res_part_rec = request.env['res.partner'].sudo().search([
            ('email', '=', res_partner_data['email_from']),
            ('company_name', '=', res_partner_data['partner_name'])])

        res_part_email = request.env['res.partner'].sudo().search([
            ('email', '=', res_partner_data['email_from'])], limit=1)

        # if len(res_part_rec) == 0 and res_part_email:
        #     print('Company change detected!')

        print(res_part_email)

        print('Verified?')
        print(res_part_email[0].is_verified)

        id_record = self.insert_record(
            request,
            model_record,
            res_partner_data,
            '',
            ''
        )

        if len(res_part_email) > 0 and len(res_part_rec) == 0 and res_part_email[0].is_verified == True:
            print('Company change detected')

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

            res_partner_dict['name'] = res_partner_data['contact_name']
            res_partner_dict['display_name'] = res_partner_data['contact_name']
            res_partner_dict['email'] = res_partner_data['email_from']
            res_partner_dict['company_name'] = res_partner_data['partner_name']
            res_partner_dict['category_id'] = [[6, False, [cat_id]]]
            # res_partner_dict['parent_id'] = res_part_email[0].id
            if 'phone' in res_partner_data:
                res_partner_dict['phone'] = res_partner_data['phone']

            print('Here')

            update_parent_partner = request.env['res.partner'].sudo().search([
                ('id', '=', res_part_email[0].id)])

            print(update_parent_partner)
            if update_parent_partner and len(update_parent_partner) > 0:
                update_parent_partner[0].category_id = False

                update_parent_partner_comp = request.env['res.partner'].sudo().search([
                    ('id', '=', res_part_email[0].parent_id.id)])

                if update_parent_partner_comp and len(update_parent_partner_comp) > 0:
                    update_parent_partner_comp[0].category_id = False

            res_partner_company_dict = res_partner_dict.copy()
            res_partner_company_dict.pop('email')
            res_partner_company_dict.pop('company_name')
            # res_partner_company_dict.pop('parent_id')
            if 'phone' in res_partner_company_dict:
                res_partner_company_dict.pop('phone')

            res_partner_company_dict['name'] = res_partner_data['partner_name']
            res_partner_company_dict['display_name'] = res_partner_data['partner_name']
            res_partner_company_dict['customer'] = False
            res_partner_company_dict['is_company'] = True
            res_partner_company_dict['company_type'] = 'company'

            # res_partner_dict['parent_id'] = id_record_res_company

            id_record_res = self.insert_record(
                request,
                request.env['ir.model'].search(
                    [('model', '=', 'res.partner')]),
                res_partner_dict,
                '',
                ''
            )

            res_partner_company_dict['child_ids'] = [
                [6, 'virtual_1798', [id_record_res]]]
            id_record_res_company = self.insert_record(
                request,
                request.env['ir.model'].search(
                    [('model', '=', 'res.partner')]),
                res_partner_company_dict,
                '',
                ''
            )

            if update_parent_partner and len(update_parent_partner) > 0:
                update_parent_partner[0].child_ids = [
                    [6, 'virtual_1798', [id_record_res]]]

            id_record = self.insert_record(
                request,
                model_record,
                res_partner_data,
                '',
                ''
            )
            if id_record:
                self.insert_attachment(
                    model_record,
                    id_record,
                    ''
                )
            if id_record and model_name == "crm.lead":
                crm_lead_obj = request.env['crm.lead'].sudo().search([
                    ('id', '=', id_record)]
                )
                email_data = crm_lead_obj.email_from + "####" +\
                    crm_lead_obj.contact_name + "####" +\
                    str('') + "####" +\
                    str('') + "####" +\
                    str('')+"####" + \
                    str(res_partner_data['send_mail']) + "####" + \
                    str(res_partner_data['request_gdpdr']) + "####" + \
                    str(id_record) + "####" + \
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
                ).sudo().send_mail(id_record)

        request.env.ref('website_contact_extend.email_template_onchange_data').sudo(
        ).send_mail(id_record)

        request.session['form_builder_model_model'] = model_record.model
        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id'] = id_record

        return json.dumps({'id': id_record})
