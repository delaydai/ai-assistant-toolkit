from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-assistant-toolkit",
    version="1.0.0",
    author="AI Assistant",
    author_email="noreply@example.com",
    description="A toolkit created and maintained by AI Assistant to improve productivity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ai-assistant/ai-assistant-toolkit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        # 基础依赖
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.900",
        ],
        "full": [
            "pandas>=1.3",
            "numpy>=1.20",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-cost-calc=ai_assistant_toolkit.cli:cost_calc",
            "file-organizer=ai_assistant_toolkit.cli:file_organizer",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/ai-assistant/ai-assistant-toolkit/issues",
        "Funding": "https://github.com/sponsors/ai-assistant",
        "Source": "https://github.com/ai-assistant/ai-assistant-toolkit",
    },
)