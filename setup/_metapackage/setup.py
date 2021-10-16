import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-data-protection",
    description="Meta package for oca-data-protection Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-privacy',
        'odoo13-addon-privacy_consent',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
