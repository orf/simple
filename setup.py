from setuptools import setup

setup(
    name='simple',
    version='2',
    packages=['simple'],
    url='',
    license='',
    author='Orf',
    author_email='tom@tomforb.es',
    description='',
    install_requires=["flask", "flask_seasurf", "pony", "markdown", "python_dateutil",
              "flask_basicauth", 'requests', 'flask_script'],
    entry_points={
        'console_scripts': ['simple=simple.commands:main']
    }
)
