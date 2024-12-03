from setuptools import setup, find_packages

setup(
    name='warp',
    version='2.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask>=2.2.0,<2.3.0',
        'flask-sqlalchemy>=3.0.0',
        'jsonschema',
        'xlsxwriter',
        'orjson',
        'ldap3',
        'werkzeug>=2.2.0',
        'sqlalchemy>=1.4.0'
    ],
    python_requires='>=3.8',
    description='Warp booking system',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/warp',
)
