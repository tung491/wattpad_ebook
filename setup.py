try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requisites = []

setup(
    name='wattpad_ebook',
    version='0.0.7',
    description='Generate ebook from Wattpad, '
                'upload into Google Drive and send to Kindle',
    author='Do Son Tung',
    url='https://github.com/tung491/wattpad_ebook',
    author_email='dosontung007@gmail.com',
    packages=['wattpad_ebook'],
    license='MIT',
    install_requires=['requests_html'],

    entry_points={
        'console_scripts': [
            'wattpad-ebook=wattpad_ebook.wattpad_ebook:cli'
        ],
    }
)
