import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-data-protection",
    description="Meta package for oca-data-protection Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-contact_search_form',
        'odoo11-addon-privacy',
        'odoo11-addon-privacy_consent',
        'odoo11-addon-privacy_partner_report',
        'odoo11-addon-website_contact_extend',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
