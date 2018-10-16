# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json
from odoo import http

from odoo.addons.web.controllers.main import serialize_exception
from odoo.addons.web.controllers.main import Reports


class ReportsExtended(Reports):
    # HACK of https://github.com/odoo/odoo/pull/24964

    @http.route()
    @serialize_exception
    def index(self, action, token):
        action = json.loads(action)
        if "data" in action.keys() and action["data"]:
            action["datas"] = action["data"]
        action = json.dumps(action)
        return super(ReportsExtended, self).index(action, token)
