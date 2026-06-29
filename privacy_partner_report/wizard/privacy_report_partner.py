# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# Copyright 2025 Juan Jose Bautista - Aulora AG.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import ast
from itertools import zip_longest

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class PrivacyPartnerReport(models.TransientModel):
    """Class for PrivacyPartnerReport"""

    _name = "privacy.partner.report"
    _description = "Privacy Partner Report"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
        context={"active_test": False},
    )

    table_ids = fields.Many2many(
        "privacy.partner.data",
        string="Models with related partner data",
    )

    def chunks_of_list(self, lst, n):
        """this function split the provided list into a list of list"""
        args = [iter(lst)] * n
        return [
            list(filter(None, group)) for group in zip_longest(*args, fillvalue=None)
        ]

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """updates Models with related partner data when partner is changed"""
        if self.partner_id:
            self.table_ids = False
            data = self._get_tables_from_partner(self.partner_id)
            names = self._get_table_names(data)
            tables = self.env["privacy.partner.data"]
            for name in sorted(names):
                vals = self._get_default_table(
                    name=name,
                    data=[t for t in data if t[0] == name and not t[5]],
                )
                if vals:
                    query = """
                                INSERT INTO privacy_partner_data (
                                name, model_id, count_rows,
                                field_type, res_ids)
                                VALUES (%s, %s, %s, %s, %s);
                             """
                    # if the res_id is greater than 500  the size
                    # of the index row you're trying to insert
                    # exceeds the maximum size allowed by the database
                    # to avoid this we split the res_id list

                    if len(vals.get("res_ids")) > 500:
                        res_ids = vals.get("res_ids")
                        list_result = self.chunks_of_list(res_ids, 500)
                        for result in list_result:
                            self._cr.execute(
                                query,
                                (
                                    vals.get("name"),
                                    vals.get("model_id"),
                                    len(result),
                                    vals.get("field_type"),
                                    result,
                                ),
                            )
                            table_data_created = self.env[
                                "privacy.partner.data"
                            ].search([], order="id DESC", limit=1)
                            self.table_ids |= table_data_created
                    else:
                        self._cr.execute(
                            query,
                            (
                                vals.get("name"),
                                vals.get("model_id"),
                                vals.get("count_rows"),
                                vals.get("field_type"),
                                vals.get("res_ids"),
                            ),
                        )
                        table_data_created = self.env["privacy.partner.data"].search(
                            [], order="id DESC", limit=1
                        )
                        self.table_ids |= table_data_created

            if not self.table_ids:
                self.table_ids = tables
        else:
            self.table_ids = self.env["privacy.partner.data"]
        return {
            "domain": {
                "table_ids": [("id", "in", self.table_ids.ids)],
            },
        }

    @api.onchange("company_id")
    def _onchange_company_id(self):
        """updates partner domain  when company_id is changed
        or set default company as users company"""
        if not self.company_id:
            self.company_id = self.env.user.company_id
        return {
            "domain": {
                "partner_id": [("company_id", "in", [self.company_id.id, False])],
            },
        }

    def button_export_xlsx(self):
        """checks if the partner have data if user has no data raise
        a user error else triggers the report creation"""

        self.ensure_one()
        if not self.table_ids:
            raise UserError(_("No data for this partner."))
        return self.check_report(xlsx_report=True)

    def _build_contexts(self, data):
        result = {}
        result["partner_id"] = data["form"]["partner_id"][0] or False
        result["company_id"] = data["form"]["company_id"][0] or False
        result["table_ids"] = (
            "table_ids" in data["form"] and data["form"]["table_ids"] or False
        )
        return result

    @staticmethod
    def _transform_binary(binary):
        # TODO: Implement if needed
        return False

    def _clean_data(self, model, rows):
        """get the values of the label of table
        and generate the rows for Excel report"""
        cleaned_rows = []
        for i, row in enumerate(rows):
            cleaned_rows.append({})
            for key, value in row.items():
                # added try except to ignore errors caused due to missing
                # or deleted records
                try:
                    if self.env[model]._fields.get(key):
                        label_name = self.env[model]._fields.get(key).string or key
                    else:
                        label_name = key
                    label = label_name
                    if (
                        self.env[model]._fields.get(key)
                        and self.env[model]._fields.get(key).store
                    ):
                        if "many2one" == self.env[model]._fields[key].type:
                            comodel = self.env[model]._fields[key].comodel_name
                            if value:
                                record = self.env[comodel].sudo().browse(value)
                                cleaned_rows[i][label] = record.display_name
                            else:
                                cleaned_rows[i][label] = rows[i][key]
                        elif "binary" == self.env[model]._fields[key].type:
                            binary = self._transform_binary(rows[i][key])
                            if binary:
                                cleaned_rows[i][label] = binary
                        elif "2many" not in self.env[model]._fields[key].type:
                            cleaned_rows[i][label] = rows[i][key]
                except Exception:
                    continue
        return cleaned_rows

    def check_report(self, xlsx_report=False):
        """get the data from the wizard form to
        create the report"""
        self.ensure_one()
        data = {}
        data["ids"] = self.env.context.get("active_ids", [])
        data["model"] = self.env.context.get("active_model", "ir.ui.menu")
        data["form"] = self.read(["partner_id", "company_id", "table_ids"])[0]
        used_context = self._build_contexts(data)
        data["form"]["id"] = str(data["form"]["id"])
        data["form"]["used_context"] = dict(
            used_context, lang=self.env.context.get("lang", "en_US")
        )

        return self._print_report(data=data, xlsx_report=xlsx_report)

    def compute_data_for_report(self, data):
        """
        checks if Form content  is present,if partner is present
        """
        if not data.get("form"):
            raise UserError(
                _("Form content is missing, this report cannot be printed.")
            )
        partner = data["form"].get("partner_id", False)
        if not partner:
            raise UserError(_("No provided partner."))
        partner = self.env["res.partner"].sudo().browse(partner[0])
        tables = data["form"].get("table_ids", False)
        if tables:
            tables = self.env["privacy.partner.data"].browse(tables)
            tables = self._get_rows_from_tables(tables, partner)
        data.update(
            {
                "tables": tables,
            }
        )
        return data

    def _exclude_column(self, model, column):
        """exclude column"""
        # https://github.com/odoo/odoo/issues/24927
        if model in ("mail.compose.message", "survey.mail.compose.message"):
            if column in ("needaction_partner_ids", "starred_partner_ids"):
                return True
        # feel free to add more specific cases meanwhile the issue is not fixed
        return False

    def _get_default_table(self, name, data):
        """get Models with related partner data"""
        if data:
            field_type = data[0][4]
            res = self.env[data[0][1]]
            for t in data:
                res |= self.env[t[1]].sudo().browse(t[3])
            if res:
                values = {
                    "name": name,
                    "model_id": self.env["ir.model"]
                    .sudo()
                    .search([("model", "=", res._name)])
                    .id,
                    "count_rows": len(res.ids),
                    "field_type": field_type,
                    "res_ids": res.ids,
                }
                return values
        return {}

    def _get_model_from_table(self, table, partner):
        """get model from table"""
        new_tables = {}
        for model in table.model_id:
            rows = self._get_rows_from_model(model, partner)
            new_tables[model.display_name] = rows
        return new_tables

    def _get_rows_from_model(self, model, partner):
        """gets row from model"""
        lines = self.env[model.model]
        columns = [
            k
            for k, v in self.env[model.model]._fields.items()
            if v.comodel_name == "res.partner"
            and v.store
            and not self._exclude_column(model.model, k)
        ]
        for column in columns:
            try:
                if "active" in self.env[model.model]._fields:
                    domain = [
                        (column, "=", partner.id),
                        "|",
                        ("active", "=", False),
                        ("active", "=", True),
                    ]
                else:
                    domain = [(column, "=", partner.id)]
                lines |= self.env[model.model].sudo().search(domain)
            except Exception:
                continue
        rows = lines.sudo().read(load=False)
        rows = self._clean_data(model.model, rows)
        return rows

    def _get_rows_from_tables(self, tables, partner):
        new_tables = {}
        for table in tables:
            data_table = self._get_model_from_table(table, partner)
            new_tables[str(table.name)] = data_table
        return new_tables

    def _get_table_names(self, data):
        """get the name of the table"""
        names = []
        for t in data:
            if t[1] == "res.partner" and t[3] == []:
                t[3] = [self.partner_id.id]
            if t[3] and not t[5] and t[0] not in names:
                names.append(t[0])
        return names

    def _get_tables_from_partner(self, partner):
        """gets Models with related partner data"""
        modules = [x for x in self.env.registry.keys()]
        with_active = []
        without_active = []
        for module in modules:
            if "active" in self.env[module]._fields:
                with_active.append(module)
            else:
                without_active.append(module)

        tables1 = [
            t[0]
            for t in [
                [
                    [
                        self.env[m]._table,
                        m,
                        k,
                        self.env[m]
                        .sudo()
                        .search(
                            [
                                (k, "=", partner.id),
                                "|",
                                ("active", "=", False),
                                ("active", "=", True),
                            ]
                        )
                        .ids,
                        v.type,
                        self.env[m]._transient,
                    ]
                    for k, v in self.env[m]._fields.items()
                    if v.comodel_name == "res.partner"
                    and self.env[m]._auto
                    and v.store
                    and not self._exclude_column(m, k)
                ]
                for m in [x for x in with_active]
            ]
            if t
        ]
        tables2 = [
            t[0]
            for t in [
                [
                    [
                        self.env[m]._table,
                        m,
                        k,
                        self.env[m].sudo().search([(k, "=", partner.id)]).ids,
                        v.type,
                        self.env[m]._transient,
                    ]
                    for k, v in self.env[m]._fields.items()
                    if v.comodel_name == "res.partner"
                    and self.env[m]._auto
                    and v.store
                    and not self._exclude_column(m, k)
                ]
                for m in [x for x in without_active]
            ]
            if t
        ]

        final_table = tables1 + tables2
        for i, t in enumerate(final_table):
            if t[4] == "many2many":
                if t[3]:
                    relation = self.env[t[1]]._fields[t[2]].relation
                    if relation:
                        final_table[i][0] = relation
        return final_table

    def _print_report(self, data, xlsx_report=False):
        """function to print report"""
        records = self.env[data["model"]].sudo().browse(data.get("ids", []))
        if xlsx_report:
            return (
                self.env.ref("privacy_partner_report.report_partner_xlsx")
                .with_context(landscape=True)
                .report_action(records, data=data)
            )


class PrivacyPartnerData(models.TransientModel):
    """Class that has basic information of the users"""

    _name = "privacy.partner.data"
    _description = "Privacy Partner Data"

    name = fields.Char(
        string="Database Table",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        ondelete="cascade",
        string="Models",
    )
    field_type = fields.Char(
        string="Type",
    )
    count_rows = fields.Integer(
        default=0,
        string="Number of lines",
    )
    res_ids = fields.Char(
        "Related Document IDs", index=True, help="List of Related Document IDs"
    )

    def action_view_records(self):
        """This opens a window to show the records"""
        self.ensure_one()
        modified_string = self.res_ids.replace("{", "[").replace("}", "]")
        if "active" in self.env[self.model_id.model]._fields:
            domain = [
                ("id", "in", ast.literal_eval(modified_string)),
                "|",
                ("active", "=", False),
                ("active", "=", True),
            ]
        else:
            domain = [("id", "in", ast.literal_eval(modified_string))]
        response = {
            "name": self.model_id.display_name,
            "type": "ir.actions.act_window",
            "res_model": self.model_id.model,
            "view_mode": "list,form",
            "domain": domain,
            "target": "current",
            "context": {"delete": True},
        }
        return response
