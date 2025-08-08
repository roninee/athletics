# setup.py
from setuptools import setup, find_packages

setup(
    name="mkdocs-section-cards",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "beautifulsoup4",
    ],
    entry_points={
        "mkdocs.plugins": [
            "section-cards = mkdocs_section_cards.plugin:SectionCardsPlugin",
        ]
    },
)
