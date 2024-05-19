import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'GameTime'
copyright = '2024, Colin Cai, Abdalla Eltayeb, Shaokai Lin, Andrew Zhang'
author = 'Colin Cai, Abdalla Eltayeb, Shaokai Lin, Andrew Zhang'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
              'sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'numpydoc',]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
autosummary_generate = False

html_theme = 'alabaster'
html_static_path = []