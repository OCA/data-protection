# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Base Export Anonymize",
    "description": """
        Anonymize certain fields for a group of users when exporting them
        directly or via relational fields.
        """,
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://acsone.eu",
    "depends": ["base"],
    "data": [
        "data/ir_config_parameter.xml",
        "security/groups.xml",
        "security/ir_model_fields_export_anonymize.xml",
        "views/ir_model_fields.xml",
        "views/ir_model_fields_export_anonymize.xml",
    ],
}
