import sys
from setuptools import setup, Extension

# Define compilation flags for multi-threading across different OS compilers
if sys.platform == "win32":
    compile_args = ["/openmp", "/O2"]
    link_args = []
else:
    compile_args = ["-fopenmp", "-O3", "-march=native"]
    link_args = ["-fopenmp"]

module = Extension(
    "guardog_core",
    sources=["engine.c"],
    extra_compile_args=compile_args,
    extra_link_args=link_args,
)

setup(
    name="guardog",
    version="1.0.0",
    description="Hyperscale Multi-Threaded DFA Zero-Copy Security Engine",
    ext_modules=[module],
    py_modules=["guardog"],
    install_requires=[],
)