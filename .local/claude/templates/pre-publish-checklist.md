# Pre-Publish Checklist

Before shipping to production, public repo, or package registry.

---

## Code Quality

- [ ] All tests pass
- [ ] No skipped or ignored tests without documented reason
- [ ] Type checking passes (mypy/tsc/etc.)
- [ ] Linting passes (no warnings)
- [ ] No TODO comments without linked issues
- [ ] No debug code (print statements, console.log, debugger)
- [ ] No commented-out code

## Security

- [ ] No secrets in code (grep for API_KEY, SECRET, PASSWORD, TOKEN)
- [ ] No secrets in git history
- [ ] Dependencies are pinned to specific versions
- [ ] No known vulnerable dependencies (npm audit / pip-audit / snyk)
- [ ] Input validation on all user-facing inputs
- [ ] Authentication/authorization on protected routes

## Documentation

- [ ] README is accurate and current
- [ ] Installation instructions work on a fresh clone
- [ ] API documentation matches implementation
- [ ] Breaking changes are documented
- [ ] Changelog updated

## Git & Version

- [ ] Version number bumped appropriately (semver)
- [ ] Git history is clean (no WIP commits)
- [ ] Branch is rebased/merged with main
- [ ] CI passes on all platforms
- [ ] Tag created for release

## Fresh Clone Test

```bash
# Clone to temp directory
cd $(mktemp -d)
git clone [repo-url] .

# Install and verify
[install command]
[test command]
[run command]
```

**This must work.** If it doesn't, you're shipping broken.

---

## Package-Specific

### Python (PyPI)
- [ ] `pyproject.toml` metadata complete
- [ ] `python -m build` succeeds
- [ ] `twine check dist/*` passes
- [ ] Test on TestPyPI first

### Node (npm)
- [ ] `package.json` metadata complete
- [ ] `npm pack` and inspect contents
- [ ] `.npmignore` or `files` field set correctly
- [ ] Test with `npm link` in another project

### CLI Tools
- [ ] Help text is accurate
- [ ] All subcommands work
- [ ] Exit codes are correct (0=success, non-zero=failure)
- [ ] Errors go to stderr, output to stdout

---

## Post-Publish

- [ ] Verify package installs correctly
- [ ] Verify basic functionality in clean environment
- [ ] Announce release (if applicable)
- [ ] Monitor for immediate issues (logs, error reports)

---

## The Fresh Clone Test (Detailed)

This is the most important check. It catches:
- Missing dependencies
- Hardcoded paths
- Untracked files that should be committed
- Build artifacts that should be generated

```bash
# Create isolated test environment
cd $(mktemp -d)
echo "Testing in: $(pwd)"

# Clone fresh
git clone [your-repo] .

# Follow YOUR OWN README instructions exactly
# Don't use any knowledge from development

# Run tests
[test command from README]

# Run the actual tool/app
[run command from README]

# Clean up
cd -
rm -rf [temp-dir]
```

If any step fails, **do not publish**. Fix it first.
