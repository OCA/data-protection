## To anonymize a partner record:

NOTE:  **Make sure the user has permission** to anonymize partner records. Please check the Configuration file for details on how to grant permission.

1. Go to the **Contacts App** in Odoo.
2. Select the partner record you want to anonymize.
3. Go to **Actions** → **Anonymize (GDPR)**.
4. A confirmation wizard will appear. Press the **"Confirm"** button to proceed.

Once you confirm, Odoo will anonymize the partner's record and all related child records, including:
- Chatter messages and attachments
- Linked `res.users` (user) records, if applicable

**Important:**
- The anonymization operation **cannot be undone**.
- Please be aware that once the data is anonymized, it cannot be restored, so proceed carefully.
- You carry full responsibility for using the module's features, in line with GDPR compliance.
