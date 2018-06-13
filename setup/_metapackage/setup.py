import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-data-protection",
    description="Meta package for oca-data-protection Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-privacy',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
