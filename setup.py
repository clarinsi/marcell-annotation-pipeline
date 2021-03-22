from distutils.core import setup

setup(
    name='marcell-sl-pipeline',
    version='0.2.0',
    description='Pipeline used for annotation of Slovenian text corpora, composed for the MARCELL sustainability project.',
    author='Mihael Šinkec',
    url='https://github.com/clarinsi/marcell-annotation-pipeline',
    install_requires=['obeliks == 1.0.3', 'classla == 1.0.0'],
    packages=['marcell_sl_pipeline'],
    package_data={'marcell_sl_pipeline': ['res/*.*']}
)
