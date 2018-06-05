# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import api, fields, models, _
from openerp.osv import fields as old_fields
from openerp.exceptions import UserError


class GDPRPartnerReport(models.TransientModel):
    _name = "gdpr.partner.report"
    _description = "GDPR Partner Report"

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
    )
    table_ids = fields.Many2many(
        comodel_name='gdpr.partner.data',
        string='Models with related partner data',
    )

    @api.multi
    @api.onchange('partner_id')
    def _onchange_table_ids(self):
        self.ensure_one()
        for report in self:
            if report.partner_id:
                data = self._get_tables_from_partner(self.partner_id)
                names = self._get_table_names(data)
                tables = self.env['gdpr.partner.data']
                for name in sorted(names):
                    vals = report._get_default_table(
                        name=name,
                        data=[t for t in data if t[0] == name and not t[5]],
                    )
                    if vals:
                        tables |= self.env['gdpr.partner.data'].create(vals)
                report.table_ids = tables
            else:
                report.table_ids = self.env['gdpr.partner.data']
            return {
                'domain': {
                    'table_ids': [
                        ('id', 'in', report.table_ids.ids)],
                },
            }

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            return {
                'domain': {
                    'partner_id': [
                        ('company_id', 'in', [self.company_id.id, False])],
                },
            }
        else:
            return {
                'domain': {
                    'partner_id': [('company_id', '=', False)],
                },
            }

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        return self.check_report()

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        return self.check_report(xlsx_report=True)

    def _build_contexts(self, data):
        result = {}
        result['partner_id'] = data['form']['partner_id'][0] or False
        result['company_id'] = data['form']['company_id'][0] or False
        result['table_ids'] = 'table_ids' in data['form'] and \
                              data['form']['table_ids'] or False
        return result

    def _clean_data(self, model, rows):
        cleaned_rows = []
        for i, row in enumerate(rows):
            cleaned_rows.append({})
            for key, value in row.items():
                label = self.env[model]._fields[key].string or key
                if 'many2' in self.env[model]._fields[key].type:
                    comodel = self.env[model]._fields[key].comodel_name
                    if value:
                        record = self.env[comodel].browse(value)
                        cleaned_rows[i][label] = str(record.display_name)
                    else:
                        cleaned_rows[i][label] = rows[i][key]
                else:
                    cleaned_rows[i][label] = rows[i][key]
        return cleaned_rows

    @api.multi
    def check_report(self, xlsx_report=False):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['partner_id', 'company_id', 'table_ids'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context, lang=self.env.context.get('lang', 'en_US'))
        return self._print_report(data=data, xlsx_report=xlsx_report)

    @api.multi
    def compute_data_for_report(self, data):
        if not data.get('form'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))
        partner = data['form'].get('partner_id', False)
        if not partner:
            raise UserError(
                _("No provided partner."))
        partner = self.env['res.partner'].browse(partner[0])
        tables = data['form'].get('table_ids', False)
        if tables:
            tables = self.env['gdpr.partner.data'].browse(tables)
            tables = self._get_rows_from_tables(tables, partner)
        data.update({'tables': tables, })
        return data

    def _exclude_column(self, model, column):

        # To remove in v10:
        # (non-stored function fields should have _fnct_search)
        column_info = self.env[model]._columns.get(column)
        next_model = self.env[model]
        while not column_info and column in next_model._inherit_fields:
            next_model = self.env[next_model._inherit_fields[column][0]]
            column_info = next_model._columns.get(column)
        if isinstance(column_info, old_fields.function) \
                and not column_info.store and not column_info._fnct_search:
            return True

        # https://github.com/odoo/odoo/issues/24927
        if model in ('mail.compose.message', 'survey.mail.compose.message'):
            if column in ('needaction_partner_ids', 'starred_partner_ids'):
                return True
        return False

    def _get_default_table(self, name, data):
        if data:
            data_type = data[0][4]
            res = self.env[data[0][1]]
            for t in data:
                res |= self.env[t[1]].browse(t[3])
            if res:
                values = {
                    'name': name,
                    'model_id': self.env['ir.model'].search(
                        [('model', '=', res._name)]).id,
                    'count_rows': len(res.ids),
                    'type': data_type,
                }
                return values
        return {}

    def _get_model_from_table(self, table, partner):
        new_tables = {}
        for model in table.model_id:
            rows = self._get_rows_from_model(model, partner)
            new_tables[str(model.display_name)] = rows
        return new_tables

    def _get_rows_from_model(self, model, partner):
        cr = self.env.cr
        lines = self.env[model.model]
        columns = [k for k, v in self.env[model.model]._fields.items()
                   if v.comodel_name == 'res.partner' and
                   not self._exclude_column(model.model, k)]
        for column in columns:
            lines |= self.env[model.model].search([(column, '=', partner.id)])
        line_ids = ', '.join([str(i) for i in lines.ids])
        query = "SELECT * FROM %s WHERE id IN (%s)" % (
            model.model.replace('.', '_'), line_ids)
        cr.execute(query)
        rows = cr.dictfetchall()
        rows = self._clean_data(model.model, rows)
        return rows

    def _get_rows_from_tables(self, tables, partner):
        new_tables = {}
        for table in tables:
            data_table = self._get_model_from_table(table, partner)
            new_tables[str(table.name)] = data_table
        return new_tables

    def _get_table_names(self, data):
        names = []
        for t in data:
            if t[3] and not t[5] and t[0] not in names:
                names.append(t[0])
        return names

    def _get_tables_from_partner(self, partner):
        tables = [t[0] for t in [
            [[self.env[m]._table, m, k, self.env[m].sudo().search(
                [(k, '=', partner.id)]).ids, v.type, self.env[m]._transient]
             for k, v in self.env[m]._fields.items()
             if v.comodel_name == 'res.partner' and self.env[m]._auto and
             not self._exclude_column(m, k)]
            for m in [x for x in self.env.registry.keys()]] if t]
        for i, t in enumerate(tables):
            if t[4] == 'many2many':
                if t[3]:
                    relation = self.env[t[1]]._fields[t[2]].relation
                    if relation:
                        tables[i][0] = relation
        return tables

    def _print_report(self, data, xlsx_report=False):
        records = self.env[data['model']].browse(data.get('ids', []))
        processed_data = self.compute_data_for_report(data)
        if xlsx_report:
            kkk = self.env['report'].with_context(landscape=True).get_action(
                records=records, report_name='gdpr.report_partner_xlsx',
                data=processed_data)
            return kkk
        else:
            return self.env['report'].with_context(landscape=True).get_action(
                records=records, report_name='gdpr.report_partner',
                data=processed_data)


class GDPRPartnerData(models.TransientModel):
    _name = "gdpr.partner.data"
    _description = "GDPR Partner Data"

    name = fields.Char(
        string='Database Table',
    )
    model_id = fields.Many2one(
        comodel_name='ir.model',
        ondelete='cascade',
        string='Models',
    )
    type = fields.Char(
        string="Type",
    )
    count_rows = fields.Integer(
        default=0,
        string='Number of lines',
    )
