# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Base Export Anonymize",
    "summary": """
        Anonymize certain fields for a group of users when exporting them
        directly or via relational fields.
        """,
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/data-protection",
    "depends": ["base"],
    "data": [
        "data/ir_config_parameter.xml",
        "security/groups.xml",
        "security/ir_model_fields_export_anonymize.xml",
        "views/ir_model_fields.xml",
        "views/ir_model_fields_export_anonymize.xml",
    ],
}
