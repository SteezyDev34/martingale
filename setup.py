from setuptools import setup

APP = ['40a 1 PROBA.py']
OPTIONS = {
    'argv_emulation': True,
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app','unicode','pandas', 'httplib2', 'googleapiclient', 'numpy', 'pygsheets', 'rubicon', 'selenium', 'PyInstaller', 'certifi', 'pytz'],
)