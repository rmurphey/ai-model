# Branch Protection Setup Guide

## Recommended Branch Protection Rules for `main` branch

To ensure code quality and prevent breaking changes to the financial modeling engine, configure the following branch protection rules in your GitHub repository settings:

### Navigation
Go to: **Settings** → **Branches** → **Add rule** for `main` branch

### Required Settings

#### ✅ **Require a pull request before merging**
- [x] Require approvals: **1**
- [x] Dismiss stale PR approvals when new commits are pushed
- [x] Require review from code owners (optional)
- [x] Restrict pushes that create new commits to admins and service accounts

#### ✅ **Require status checks to pass before merging**
- [x] Require branches to be up to date before merging
- **Required status checks:**
  - `test (3.9)` - Python 3.9 tests
  - `test (3.10)` - Python 3.10 tests  
  - `test (3.11)` - Python 3.11 tests
  - `test (3.12)` - Python 3.12 tests
  - `test (3.13)` - Python 3.13 tests
  - `quick-test` - PR quick validation
  - `test-import-integrity` - Import validation
  - `lint-and-format` - Code quality checks

#### ✅ **Restrict pushes that create new commits**
- [x] Restrict pushes that create new commits
- **Allowed actors:** Repository administrators only

#### ✅ **Additional Protections**
- [x] Require linear history (optional, for clean git history)
- [x] Include administrators (enforce rules for all users)

### Why These Rules Matter

**For Financial Modeling Integrity:**
- Prevents breaking changes to calculation logic
- Ensures all 109+ business logic tests pass before merge
- Validates mathematical accuracy across Python versions
- Requires code review for sensitive financial calculations

**For Development Workflow:**
- Maintains code quality with automated linting
- Prevents merge conflicts with up-to-date requirement
- Enables safe collaboration on business-critical code
- Provides fast feedback with PR-specific quick tests

### Setup Commands (if using GitHub CLI)

```bash
# Enable branch protection (requires repo admin access)
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test (3.9)","test (3.10)","test (3.11)","test (3.12)","test (3.13)","quick-test","test-import-integrity","lint-and-format"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

### Verification

After setup, verify protection is active:
1. Try pushing directly to `main` - should be blocked
2. Create a test PR - should require status checks
3. Check that failing tests block merge
4. Confirm review requirement is enforced