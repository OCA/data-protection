# Copyright 2019 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib.openupgrade import rename_xmlids


def migrate(cr, version):
    """Use a better xmlid for the provided server action."""
    rename_xmlids(cr, [
        ("privacy_consent.update_opt_out", "privacy_consent.sync_blacklist"),
    ])
