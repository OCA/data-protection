You may want to install, along with this module, one of OCA's
``mail_tracking`` module collection, such as ``mail_tracking_mailgun``, so
you can provide more undeniable proof that some consent request was sent, and
to whom.

However, the most important proof to provide is the answer itself (more than
the question), and this addon provides enough tooling for that.

Multi-database instances
~~~~~~~~~~~~~~~~~~~~~~~~

To enable multi-database support, you must load this addon as a server-wide
addon. Example command to boot Odoo::

    odoo-bin --load=web,privacy_consent
