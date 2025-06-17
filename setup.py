# Note: This file is not required for normal installation or usage.

from setuptools import setup, find_packages

setup(
    name="sage-protocol",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.21.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0.0",
        "openai>=1.0.0",
        "anthropic>=0.5.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.65.0",
        "scikit-learn>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=4.0.0",
        ],
    },
    python_requires=">=3.8",
    author="SAGE Protocol Team",
    description="Sequential Agent Goal Execution Protocol for multi-LLM workflow management",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sage",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 