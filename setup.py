import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="xumx", # Replace with your own username
    version="0.0.1",
    author="Sony",
    author_email="jeffreyca16@gmail.com",
    description="X-UMX",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JeffreyCA/ai-research-code",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'lameenc==1.2.2',
        'musdb==0.3.1',
        'museval==0.3.0',
        'requests>=2.22',
        'scipy>=1.3.1',
        'setuptools>=41.0.0',
        'norbert>=0.2.1',
        'resampy==0.2.2',
        'nnabla',
    ],
    python_requires='>=3.6',
)
