# Contributing Guide

Thank you for your interest in improving this project! Follow these steps when opening issues or submitting pull requests.

## Issues

1. **Search first** – check if a similar issue already exists.
2. **Provide details** – include relevant logs, stack traces, or screenshots.
3. **Be clear** – describe the expected and actual behavior.

## Pull Requests

1. Fork the repository and create a feature branch.
2. Make your changes following **PEP 8** style and format the code with **Black**.
3. Update tests and documentation as needed.
4. Ensure `python -m py_compile $(git ls-files '*.py')` and `python -m unittest discover -s tests -v` pass.
5. Submit the PR with a concise description of the change.

By contributing, you agree that your code will be released under the MIT License.
