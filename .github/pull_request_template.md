## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Mark the relevant option with an 'x' -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test addition or update

## Architectural Compliance Checklist

<!-- Verify all items before submitting PR -->

### Type Safety
- [ ] No `Any` types used (except in explicitly allowed files)
- [ ] No `cast()` usage
- [ ] All types properly defined using `src/type_definitions/`
- [ ] MyPy strict mode passes

### Clean Architecture
- [ ] Layer boundaries respected (domain ← application ← infrastructure ← routes)
- [ ] No circular dependencies introduced
- [ ] Repository interfaces used, not implementations
- [ ] Domain layer has no infrastructure dependencies

### Single Responsibility Principle
- [ ] Files are focused and not too large (<1200 lines)
- [ ] Functions have reasonable complexity (<50 cyclomatic complexity)
- [ ] Classes have reasonable number of methods (<30 methods)

### Testing
- [ ] Tests added for new functionality
- [ ] Existing tests still pass
- [ ] Test coverage maintained or improved
- [ ] Architectural tests pass (`pytest -m architecture`)

### Documentation
- [ ] Public APIs have docstrings
- [ ] Architecture documentation updated if needed
- [ ] Code examples provided for complex logic

## Testing

<!-- Describe the tests you ran and their results -->

- [ ] `make all` passes locally
- [ ] `pytest -m architecture` passes
- [ ] All existing tests pass
- [ ] New tests added for new functionality

## Related Issues

<!-- Link to related issues -->

Closes #

## Additional Notes

<!-- Any additional information reviewers should know -->
