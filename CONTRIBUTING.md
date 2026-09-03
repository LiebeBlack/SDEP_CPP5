# 🤝 Contributing to Sistema de Gestión de Personal

Thank you for your interest in contributing to the Sistema de Gestión de Personal! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Commit Guidelines](#commit-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [CI/CD Pipeline](#cicd-pipeline)

---

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Our Standards

- Be respectful and inclusive
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Reporting Issues

Report unacceptable behavior to the project maintainers through GitHub Issues.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- GitHub account
- Basic knowledge of Python and GUI development

### Setup Development Environment

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/SDEP_CPP5.git
   cd SDEP_CPP5
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Configure environment**
   ```bash
   copy .env.example .env
   # Edit .env with your configuration
   ```

6. **Run the application**
   ```bash
   python src/main.py
   ```

---

## 🔄 Development Workflow

### Branch Strategy

We use a modified Git Flow workflow:

- **main**: Production-ready code
- **develop**: Integration branch for features
- **canary**: Testing branch for canary deployments
- **feature/**: Feature branches
- **bugfix/**: Bug fix branches
- **hotfix/**: Emergency fixes

### Creating a Feature Branch

1. **Update develop branch**
   ```bash
   git checkout develop
   git pull origin develop
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write code following coding standards
   - Add tests for new functionality
   - Update documentation as needed

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Go to GitHub and create a PR from your feature branch to `develop`
   - Fill in the PR template
   - Wait for code review

---

## 📐 Coding Standards

### Python Code Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters
- **Indentation**: 4 spaces
- **Imports**: Grouped and sorted (isort)
- **Docstrings**: Google style
- **Type hints**: Required for all functions

### Code Formatting

We use automated tools to maintain code quality:

```bash
# Format code
black src/

# Sort imports
isort src/

# Check formatting
black --check src/
isort --check-only src/
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `EmployeeService`)
- **Functions**: snake_case (e.g., `get_employee_by_id`)
- **Variables**: snake_case (e.g., `employee_name`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_EMPLOYEES`)
- **Private members**: _leading_underscore (e.g., `_internal_method`)

### Documentation

- All functions must have docstrings
- Complex logic should have inline comments
- Update README.md for user-facing changes
- Update CHANGELOG.md for developer-facing changes

---

## 🧪 Testing Guidelines

### Writing Tests

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names
- Follow Arrange-Act-Assert pattern

### Test Structure

```python
def test_employee_creation():
    # Arrange
    employee_data = {
        "name": "John Doe",
        "position": "Teacher"
    }
    
    # Act
    employee = Employee(**employee_data)
    
    # Assert
    assert employee.name == "John Doe"
    assert employee.position == "Teacher"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_employee.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_employee.py::test_employee_creation
```

### Test Categories

- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **GUI tests**: Test user interface elements
- **Critical tests**: Tests that must pass for release

---

## 📝 Commit Guidelines

### Conventional Commits

We use conventional commits for automatic versioning:

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

### Commit Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting)
- **refactor**: Code refactoring
- **test**: Test changes
- **chore**: Maintenance tasks
- **perf**: Performance improvements
- **ci**: CI/CD changes
- **build**: Build system changes

### Examples

```bash
# Feature
git commit -m "feat(employee): add employee photo upload"

# Bug fix
git commit -m "fix(database): resolve connection timeout issue"

# Documentation
git commit -m "docs(readme): update installation instructions"

# Breaking change
git commit -m "feat(api)!: change user authentication flow"

# Scope
git commit -m "feat(gui): add dark mode support"
```

### Commit Message Guidelines

- Use present tense ("add" not "added")
- Use imperative mood ("move" not "moves")
- Don't capitalize first letter
- Don't end with period
- Limit to 72 characters for subject line

---

## 🔀 Pull Request Process

### PR Template

When creating a PR, fill in the template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commit messages follow guidelines
```

### PR Review Process

1. **Automated Checks**
   - CI workflow runs automatically
   - All quality checks must pass
   - Build workflow must succeed

2. **Code Review**
   - At least one approval required
   - Address review comments
   - Make requested changes

3. **Integration**
   - Merge to `develop` for features
   - Merge to `main` for releases
   - Delete feature branch after merge

### PR Best Practices

- Keep PRs focused and small
- Provide clear description of changes
- Link related issues
- Add screenshots for UI changes
- Test thoroughly before submission

---

## 🚀 CI/CD Pipeline

### Workflow Overview

The CI/CD pipeline consists of a single workflow:

1. **Build & Release** (`build.yml`)
   - Runs on every push to main/develop, on `v*` tags, and manually
   - Job 1 (`tests`): runs the pytest suite and uploads coverage
   - Job 2 (`build`, Windows): compiles the executable with PyInstaller,
     verifies it with `--selftest`, builds the Inno Setup installer,
     uploads artifacts, and publishes a GitHub Release on **every push
     to main** (continuous release, no tag required) or on `v*` tags
     (versioned release)

### CI/CD Best Practices

- Ensure all tests pass before pushing
- Use conventional commits for versioning
- Monitor workflow runs for failures
- Address security alerts promptly
- Test canary deployments thoroughly

### Workflow Status

Check workflow status:

```bash
# List recent runs
gh run list

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

### Manual Workflow Triggers

```bash
# Trigger build manually
gh workflow run build.yml

# Every push to main publishes a Release automatically (no tag needed)
git push origin main

# Optional: versioned release from a tag
git tag v1.0.3 && git push origin v1.0.3
```

---

## 🐛 Bug Reporting

### Bug Report Template

```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Screenshots
Add screenshots if applicable

## Environment
- OS: [e.g. Windows 11]
- Python Version: [e.g. 3.11]
- Application Version: [e.g. 1.0.0]

## Additional Context
Any other relevant information
```

---

## 💡 Feature Requests

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature

## Problem Statement
What problem does this solve?

## Proposed Solution
How should this be implemented?

## Alternatives
What alternatives have you considered?

## Additional Context
Any other relevant information
```

---

## 📚 Additional Resources

- [CI/CD Documentation](CI_CD_DOCUMENTATION.md)
- [Project Structure](ESTRUCTURA_PROYECTO_COMPLETO.md)
- [README](README.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## ❓ Questions?

- Create a GitHub Issue
- Contact maintainers
- Check existing documentation

---

**Thank you for contributing! 🎉**
