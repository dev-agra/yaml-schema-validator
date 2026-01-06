from setuptools import setup, find_packages

setup(
    name="yaml-schema-validator",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        "src": ["profiles/configs/*.yaml"],
    },
    install_requires=[
        "pydantic>=2.5.0",
        "ruamel.yaml>=0.18.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "yaml-validate=main:main",
        ],
    },
    python_requires=">=3.9",
)