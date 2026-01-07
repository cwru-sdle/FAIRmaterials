from setuptools import setup, find_packages

setup(
    name='FAIRmaterials',
    version='0.4.2.7',
    description='Translates several CSV files with ontological terms and corresponding data into RDF triples. These RDF triples are stored in OWL and JSON-LD files, facilitating data accessibility, interoperability, and knowledge unification. The triples are also visualized in a graph saved as an SVG. The input CSVs must be formatted with a template from a public Google Sheet; see README or vignette for more information. This is a tool used by the SDLE Research Center at Case Western Reserve University.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Alexander Harding Bradley, Priyan Rajamohan, Jonathan E. Gordon, Nathaniel Hahn, Kiefer Lin, Arafath Nihar, Hayden Cadwell, Jiana Kambo, Jayvic Jimenez, Kristen J. Hernandez, Hein Htet Aung, Brian Giera, Weiqi Yu, Mohommad Redad Mehdi, Finley Holt, Quynh Tran, Gabriel Ponon, Dan Savage, Don Brown, Jarod Kaltenbaugh, Kush Havinal, Nicholas Gray, Max Ligget, Benjamin G. Pierce, Raymond Wieser, Yangxin Fan, Tommy Ciardi, Olatunde J. Akanbi, Hadiza Iawal, Will Oltjen, Maliesha Kalutotage, Antony Lino, Van Tran, Mingjian Lu, Xuanji Yu, Abhishek Daundkar, Hope Omodolor, Mirra Rasmussen, Sameera Nalin-Venkat, Tian Wang, Rounak Chawla, Liangyi Huang, Zelin Li, Leean Jo, Jeffrey M. Yarus, Mengjie Li, Kristopher O. Davis, Yinghui Wu, Pawan K. Tripathi, Laura S. Bruckman, Erika I. Barcelos, Roger H. French',
    author_email='rxf131@case.edu',
    license='BSD-2-Clause',
    packages=find_packages(),
    install_requires=[
        'rdflib>=7.0.0',
        'pylode>=3.1.4',
        'matplotlib>=3.6.2',
        'numpy>=1.9.3',
        'graphviz>=0.20.1'
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov'
        ]
    },
    entry_points={
        'console_scripts': [
            'FAIRmaterials=FAIRmaterials.__main__:main'
        ]
    },
    python_requires='>=3.9.18',
)
