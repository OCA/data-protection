# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from odoo.report import report_sxw
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    _logger.debug("report_xlsx not installed, Excel export non functional")

    class ReportXlsx(object):
        def __init__(self, *args, **kwargs):
            pass


class ReportPartnerXlsx(ReportXlsx):

    def _search_longest_row(self, tables):
        res = 0
        for table in tables:
            for model in tables[table]:
                if len(tables[table][model]) > 0:
                    if len(tables[table][model][0]) > res:
                        res = len(tables[table][model][0])
        return res

    def generate_xlsx_report(self, workbook, data, objects):
        partner = data['form'].get('partner_id', False)
        partner = self.env['res.partner'].sudo().browse(partner[0])
        workbook.set_properties({
            'comments': 'Created with Python and XlsxWriter from Odoo'})
        sheet = workbook.add_worksheet(_('Partner Data'))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(75)
        sheet.set_column(0, self._search_longest_row(data['tables']), 25)
        title_style = workbook.add_format(
            {'bold': True, 'bg_color': '#FFFFCC', 'border': 2})
        sheet.set_row(0, None, None, {'collapsed': 1})
        sheet.write_row(1, 0, ["Partner: " + partner.display_name],
                        title_style)
        i = 3
        first_row = i+2
        for table in sorted(data['tables'].keys()):
            for model in sorted(data['tables'][table].keys()):
                rows = len(data['tables'][table][model])
                if rows:
                    style = workbook.add_format()
                    style.set_bold(True)
                    style.set_border(2)
                    sheet.write_row(i, 0, [model], style)
                    i += 1
                    j = 0
                    for column in data['tables'][table][model][0]:
                        style = workbook.add_format()
                        style.set_bold(True)
                        if j == 0:
                            style.set_left(1)
                        if j == len(data['tables'][table][model][0]) - 1:
                            style.set_right(1)
                        style.set_top(1)
                        style.set_bottom(1)
                        sheet.write_row(i, j, [column], style)
                        j += 1
                    for row in data['tables'][table][model]:
                        i += 1
                        j = 0
                        for column in row:
                            style = workbook.add_format()
                            if j == 0:
                                style.set_left(1)
                            if j == len(row) - 1:
                                style.set_right(1)
                            if i == rows + first_row - 1:
                                style.set_bottom(1)
                            if row[column]:
                                sheet.write_row(i, j, [row[column]], style)
                            else:
                                sheet.write_row(i, j, [''], style)
                            j += 1
                i += 2
                first_row = i+2


ReportPartnerXlsx(
    'report.privacy.report_partner_xlsx',
    'privacy.partner.report',
    parser=report_sxw.rml_parse
)
