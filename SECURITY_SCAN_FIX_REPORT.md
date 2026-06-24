# Security Scan Fix Report

## Root Cause
`aquasecurity/trivy-action@v0.28.0` internally calls `aquasecurity/setup-trivy@v0.2.1`. The tag `v0.2.1` was removed from the `aquasecurity/setup-trivy` repository (returns HTTP 404), so GitHub Actions could not resolve the composite action dependency.

No explicit `setup-trivy` steps exist in any workflow file — the broken reference was embedded inside `trivy-action`'s `action.yaml`.

## Fix
Upgraded `trivy-action` from `@v0.28.0` to `@v0.36.0` in `.github/workflows/ci.yml`.

`trivy-action@v0.36.0` pins `setup-trivy` to commit hash `3fb12ec12f41e471780db15c232d5dd185dcb514` (tagged `v0.2.6`), which is a valid, resolvable reference.

## Files Changed
| File | Change |
|------|--------|
| `.github/workflows/ci.yml:151` | `aquasecurity/trivy-action@v0.28.0` → `@v0.36.0` |

## Verification
- All 3 workflow YAML files pass `yaml.safe_load()` validation
- `trivy-action@v0.36.0` `action.yaml` confirms `setup-trivy` pinned to `3fb12ec...` (# v0.2.6)
- No other references to `setup-trivy` exist in `.github/workflows/`
