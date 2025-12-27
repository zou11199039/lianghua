# Draft PR: CI + qmt_client improvements

## Title
ci: add tests for QMT client, make xtquant import optional, include Python 3.13 in CI matrix

## Summary
This draft PR includes:

- Make `xtquant.xtdata` import optional so tests and CI can run in environments without xtquant installed.
- Add `tests/test_qmt_client.py` to cover start/ensure logic, retry behavior and xtdata call forwarding.
- Add `tests/test_receipt_parser_xtquant.py` additional xtquant-style receipt tests.
- Update `.github/workflows/ci.yml` matrix to include Python 3.13.

## Files changed
- `src/data/qmt_client.py` (optional import, warnings, retry wrapper)
- `tests/test_qmt_client.py` (new)
- `tests/test_receipt_parser_xtquant.py` (new)
- `.github/workflows/ci.yml` (matrix python versions)

## Tests
Local tests: `pytest` => 11 passed (2 warnings).

## How to create the Draft PR (recommended)
1. Ensure you're on branch `ci/qmt-client-tests`:
   - git checkout -b ci/qmt-client-tests
2. Commit changes and push:
   - git add -A && git commit -m "ci: add qmt_client tests; make xtquant import optional; add py3.13 to CI matrix"
   - git push -u origin ci/qmt-client-tests
3. Create a draft PR (using GitHub CLI `gh`):
   - gh pr create --draft --title "ci: add tests for QMT client, make xtquant import optional" --body-file .github/PRs/ci-qmt-client-draft.md --base main

If you prefer web UI, push the branch and open a new PR in GitHub and mark it as Draft.

## Notes / Next steps
- Consider adding a tox/matrix for more Python versions and Windows runner if we need Windows-only behavior testing.
- Once merged, we can extend the CI to run tests selectively and add linters/formatters.
