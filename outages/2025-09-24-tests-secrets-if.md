# Invalid secrets context in tests workflow

- **Date**: 2025-09-24
- **Summary**: GitHub Actions refused to run `.github/workflows/02-tests.yml` because it referenced the `secrets` context inside a step `if` expression.
- **Impact**: The "Test Suite" workflow terminated immediately on every push and pull request, so no tests or coverage ran and the badge stayed ❓.
- **Root Cause**: `if: ${{ secrets.CODECOV_TOKEN }}` is not allowed—`secrets` context cannot be used in step conditions, so the workflow validation failed before scheduling any jobs.
- **Resolution**: Promote the Codecov token into a job-level environment variable and guard the upload step with `if: ${{ env.CODECOV_TOKEN != '' }}` while passing the env value to the action.
- **Lessons**: Lint workflows for forbidden contexts (e.g., with actionlint) and rely on env-scoped flags instead of referencing `secrets` directly in conditions.
- **Links**: [Outage record](2025-09-24-tests-secrets-if.json)

## Follow-up

- `npm run test:ci` now runs `actionlint` in addition to the prompt summary
  checks so future forbidden contexts fail fast (see
  `tests/test_package_json.py::test_package_json_requires_actionlint_dev_dependency`
  and `tests/test_workflow_yaml.py::test_run_checks_invokes_actionlint`).
