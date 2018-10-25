# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class SearchLine(models.Model):
    _name = "search.line"

    name = fields.Char(string="Model Name")
    field_list = fields.Char(string="Fields Name")
    model_id = fields.Many2one('ir.model', string="Found in Model")
    record_id = fields.Integer(string="Record ID")
    search_id = fields.Many2one("dpo.view", string="Search Terms")
    record_name = fields.Char(string="Record Name",
                              compute="_compute_record_name")

    @api.multi
    def open_record(self):
        return {
            'name': _('Found record'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self.model_id.model,
            'type': 'ir.actions.act_window',
            'res_id': self.record_id,
            'target': 'new'
            }

    def _compute_record_name(self):
        for record in self:
            record_object = self.env[self.model_id.model].browse([
                self.record_id
            ])
            record.record_name = record_object.name_get()[0][1]


class DpoView(models.Model):
    _name = "dpo.view"

    name = fields.Char(string="Search Term")
    model_ids = fields.Many2many('ir.model',
                                 'dpo_view_ir_model_rel',
                                 string='Search in Model')
    search_lines = fields.One2many('search.line',
                                   'search_id',
                                   string='Search Result')

    @api.multi
    def search_string(self):
        search_line_ids = self.env['search.line'].search([
            ('search_id', '=', self.id)
        ])
        search_line_ids.unlink()
        final_list = []
        for model_id in self.model_ids:
            field_list = []
            found_match = {}
            for field_id in model_id.field_id:
                if field_id.ttype in ['char', 'html', 'text'] \
                        and field_id.store:
                    field_list.append(field_id.name)
            for field in field_list:
                records = self.env[model_id.model].search([
                    (field, 'ilike', self.name),
                    (field, '!=', '')
                ])
                for rec in records:
                    temp_list = found_match.get(rec.id, False)
                    if temp_list:
                        temp_list.append(field)
                        found_match[rec.id] = temp_list
                    else:
                        found_match[rec.id] = [field]
            for key, value in found_match.items():
                founded_json = {}
                founded_json["field_list"] = str(list(set(value)))
                founded_json["name"] = str(model_id.name)
                founded_json["model_id"] = model_id.id
                founded_json["search_id"] = self.id
                founded_json["record_id"] = key
                final_list.append(founded_json)
        if final_list:
            for vals in final_list:
                self.env['search.line'].create(vals)
