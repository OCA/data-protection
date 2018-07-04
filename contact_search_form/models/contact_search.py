# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SearchLine(models.Model):
    _name = "search.line"

    name = fields.Char(string="Model Name")
    field_list = fields.Char(string="Fields Name")
    model_id = fields.Many2one('ir.model', string="Found in Model")
    record_id = fields.Integer(string="Record ID")
    search_id = fields.Many2one("dpo.view", string="Search Terms")
    record_name = fields.Char(string="Record Name", compute="_compute_record_name")

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

    @api.one
    def _compute_record_name(self):
        for record in self:
            record_object = self.env[self.model_id.model].search([('id', '=', int(self.record_id))])
            record.record_name = record_object.name

class ItisDpoView(models.Model):
    _name = "dpo.view"

    name = fields.Char(string="Search Term")
    model_ids = fields.Many2many('ir.model', 'dpo_view_ir_model_rel', string="Search in Model")
    search_lines = fields.One2many('search.line', 'search_id', string='Search Result')

    @api.multi
    def search_string(self):
        search_line_ids = self.env['search.line'].search([('search_id', '=', self.id)])
        search_line_ids.unlink()
        found = False
        for model in self.model_ids:
            table_name = model.model.replace(".", "_")
            query = '''select * from ''' + table_name + ''' where '''
            field_list = self.env['ir.model.fields'].search([('model_id.id', '=', model.id),
                                                             ('ttype', 'in', ['char', 'html', 'text']),
                                                             ('store', '=', True)])
            for field in field_list:
                query = query + table_name + '''."''' + field.name + '''" like '%''' + self.name + '''%' or '''
            query = query[:-3]
            query += ''';'''

            self._cr.execute(query)
            colnames = [desc[0] for desc in self._cr.description]
            id_index = colnames.index("id")
            rec_id = 0
            rows = self._cr.fetchall()

            if rows:
                for rec in rows:
                    ind = 0
                    rec_id = rec[id_index]
                    founded_col = []
                    for row in rec:
                        if str(row).find(self.name) >= 0:
                            founded_col.append(colnames[ind])
                        found = True
                        ind += 1
                    fields_data = self.env['ir.model.fields'].search([('name', 'in', founded_col),
                                                                      ('model_id', '=', model.id)])
                    field_desc = []
                    for field in fields_data:
                        field_desc.append(field.field_description)
                    create_id = self.env['search.line'].create({"field_list": str(field_desc),
                                                                "name": model.name,
                                                                "model_id": int(model.id),
                                                                "search_id": int(self.id),
                                                                "record_id": int(rec_id)})
        if not found:
            raise UserError(_("No record found with "+self.name+"."))