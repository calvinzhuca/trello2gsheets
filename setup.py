from setuptools import setup, find_packages

setup(
    name='trello2gsheets',
    version='0.1',
    author='Anton Sherkhonov',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['py-trello', 'google-api-python-client',
                      'gspread', 'pyyaml', 'arrow'],
    tests_require=['mock', 'nose2', 'pep8'],
    test_suite='tests',
    entry_points = {
        'console_scripts': ['trello2gsheets=trello2gsheets.main:main'],
    },
)
