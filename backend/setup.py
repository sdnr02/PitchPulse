# This will be changed to a pyproject.toml file

from setuptools import setup, find_packages

setup(
    name="pitchpulse-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "psycopg2-binary",
        "redis",
        "python-dotenv",
        "alembic",
    ],
)