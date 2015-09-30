from setuptools import setup

setup(
    name='simpleblogging',
    version='2.0.8',
    packages=['simple'],
    url='http://github.com/orf/simple',
    license='MIT',
    author='Orf',
    author_email='tom@tomforb.es',
    description='A simple markdown based blog.',
    include_package_data=True,
    install_requires=["flask", "flask_seasurf", "pony", "markdown", "python_dateutil",
              "flask_basicauth", 'requests', 'flask_script'],
    entry_points={
        'console_scripts': ['simple=simple.commands:main']
    },
    classifiers=[
        "License :: OSI Approved :: MIT License"
    ]
)
