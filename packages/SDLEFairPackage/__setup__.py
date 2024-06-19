from setuptools import setup, find_packages

setup(
    name='your_package_name',
    version='0.1',  # Update with your version number
    packages=find_packages(),
    install_requires=[
        'rdflib',
        'pylode',
        'graphviz',
    ],
    author=['Alexander Harding Bradley', 'Priyan Rajamohan', 'Kiefer Lin'],
    author_email=['ach159@case.edu', 'bxr261@case.edu', 'kyl29@case.edu'],
    description='This package parses a FAIR Sheet Parser template from the SDLE Lab, converts it into an RDFLib and Graphviz Lab, and outputs multiple different files based on the generated ontology',
    url='https://github.com/your_username/your_package_name',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)