The module allows anonymizing contacts that represent natural persons (i.e., individuals) when they are no longer needed or when a data erasure request is received.

This module provides a method to anonymize all personally identifiable information (PII) from a `res.partner` record:
- Name (e.g., replaced with initials or a generic label) for individual contacts
- Email address
- Phone numbers
- Street and address fields
- Tax ID
- Citizen Identification
- Job position and title
- Internal Notes
- Attached images (e.g., avatar)

The anonymization preserves the partner's link to its parent company if applicable (e.g., for a B2B contact) but ensures that the individual is no longer identifiable through the remaining data or relationships.

Additionally, the module removes all chatter messages (`mail.message`) and attachments associated with the partner record, as these may contain personal information, such as communication history, internal notes, or file uploads. This ensures complete anonymization and supports full GDPR compliance.

If the partner is linked to one or more `res.users` records (e.g., as a portal user or employee), the module will anonymize these user records:
-  The user login and email are replaced with anonymized values, and the user is archived.

A log note is added to the partner record chatter to indicate the anonymization event, supporting traceability.
