import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-data-protection",
    description="Meta package for oca-data-protection Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-privacy',
        'odoo12-addon-privacy_consent',
        'odoo12-addon-privacy_partner_report',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
