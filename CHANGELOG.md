# Changelog

## 0.2.2

- switch shopping-list `add_item()` from the removed GraphQL mutation to the live REST endpoint
- align shopping-list add behavior with the confirmed `PATCH /mobile-services/shoppinglist/v2/items` API
- add coverage for both free-text and product-backed shopping-list adds

## 0.2.1

- add richer product metadata for grocery-planning use cases
- expose `original_price`, `is_bonus`, `bonus_label`, `bonus_start_date`, `bonus_end_date`, `is_organic`, and `property_labels`
- keep `original_price` empty when there is no real discount instead of mirroring the current price
- update the mock client fixtures to include bonus and biologisch examples
- expand README and product docs with the new planning-oriented product fields

## 0.2.0

- add a programmable mock controller for `MockAHClient`
- support call capture, seeded one-shot responses, and persistent mock scenarios
- add a pytest plugin for downstream packages
- complete shopping-list support with live-confirmed `get_list()`, `remove_item()`, and `clear()`
- improve English and Dutch documentation

## 0.1.0

- initial release of `python-appie`
- async AH client with login flow, token persistence, product search, receipt access, and shopping-list add
- MkDocs documentation, GitHub Pages publishing, PyPI publishing workflow, tests, linting, and pre-commit hooks
