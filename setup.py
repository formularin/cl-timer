import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cl-timer",
    version="1.1.4",
    author="Arin Khare",
    author_email="arinmkhare@gmail.com",
    description="A Cubing Timer for the Terminal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lol-cubes/cl-timer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    python_requires='>=3.7',
    entry_points = {
        'console_scripts': [
            'cl-timer = cl_timer.timer:main'
        ]
    }
)