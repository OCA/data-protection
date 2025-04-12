# Copyright (C) 2025 Cetmix OÜ
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Privacy Partner's Right to be Forgotten",
    "version": "17.0.1.0.0",
    "development_status": "Beta",
    "category": "Data Protection",
    # question for manager:
    # this is from task description. is it ok?
    "summary": "This module adds tons of cool features",
    "author": "Cetmix OÜ, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/data-protection",
    "depends": ["contacts"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "wizards/partner_anonymize_wizard_views.xml",
    ],
    "demo": ["demo/demo_partner_anonymize_data.xml"],
    "maintainers": ["halbtonjazz"],
    "installable": True,
    "application": False,
}
