# Changelog

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.7] - September 16th 2021

- Another edge case involving multi-line comments and trailing slashes

## [1.0.6] - September 16th 2021

- Fix edge case where commas in multiline asserts don't have trailing slashes but should
- Two spaces between trailing slashes and inline comments

## [1.0.5] - July 26th 2021

- If assert is alone, combine the next line with it

## [1.0.4] - July 25th 2021

- `import pytest` is next to other imports
- Rewrite multiline asserts with fewer slashes

## 1.0.3 - July 22nd 2021

- pytest.approx

## 1.0.2

*(Skipped, had a mistake in it)*

## 1.0.1 - July 17th 2021

- Skipping
- Expected failures
- setupClass / teardownClass

## 1.0.0 - July 14th 2021

- Test class name
- setUp / TearDown
- Simple asserts
- Multi-line asserts
