# Claude Development Guidelines

This file contains project-specific instructions for Claude Code when working on this AI impact analysis tool.

## Commit Guidelines

### Commit Often and Atomically
- Make frequent, small commits for each logical change
- Each commit should represent a single, complete unit of work
- Avoid bundling unrelated changes in a single commit
- Use descriptive commit messages that explain the "why" not just the "what"

Examples of atomic commits:
- "Add export functionality to run_analysis.py"
- "Update README to document Claude command usage"  
- "Remove deprecated HTML visualization dependencies"

### Always Update README Before Pushing
- **MANDATORY**: Update README.md whenever functionality changes
- Document new features, commands, or usage patterns immediately
- Keep examples current and accurate
- Ensure project structure documentation matches reality
- Update export/usage instructions when CLI changes

## Workflow Requirements

1. **Make code changes**
2. **Update README.md** to reflect changes (if applicable)
3. **Test functionality** to ensure it works
4. **Commit atomically** with clear messages
5. **Push to repository**

## Documentation Standards

- Keep README examples current and working
- Document all CLI commands and options
- Include export functionality details
- Maintain accurate project structure diagrams
- Update usage examples when interfaces change

## Quality Checks

Before any push:
- [ ] README reflects current functionality
- [ ] All examples in README are tested and working
- [ ] Commit messages are descriptive and atomic
- [ ] No unrelated changes bundled together
- [ ] Did the model change? Bump the version.

## Planning

- Never include an implementation timeline

## Behavior and Tone

- Never say "you're right" or any variation thereof.
- Always Read a file before you attempt to Update it.
- Never say an issue is fixed without TDD-ing your way to a solution.