# Contributing to Barclays Credit Intelligence Platform

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 🌟 Ways to Contribute

- **Bug Reports:** Report bugs via GitHub Issues
- **Feature Requests:** Suggest new features or improvements
- **Code Contributions:** Submit pull requests for bug fixes or features
- **Documentation:** Improve or add documentation
- **Testing:** Write tests or improve test coverage
- **Code Review:** Review pull requests from other contributors

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/barclays-credit-platform.git
cd barclays-credit-platform

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/barclays-credit-platform.git
```

### 2. Set Up Development Environment

```bash
# Copy environment file
cp .env.example .env

# Start services
docker-compose up --build

# Or for local development:
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

## 📝 Development Guidelines

### Code Style

**Python (Backend):**
- Follow PEP 8 style guide
- Use type hints where possible
- Maximum line length: 120 characters
- Use meaningful variable and function names
- Add docstrings to functions and classes

**TypeScript/React (Frontend):**
- Follow Airbnb React/JSX Style Guide
- Use functional components with hooks
- Use TypeScript for type safety
- Use meaningful component and variable names
- Keep components small and focused

### Commit Messages

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(ml): add support for ensemble models

fix(auth): resolve JWT token expiration issue

docs(readme): update installation instructions
```

### Testing

**Backend Tests:**
```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

**Frontend Tests:**
```bash
cd frontend
npm test
npm run test:coverage
```

**Integration Tests:**
```bash
./run_tests.sh
```

### Code Review Checklist

Before submitting a PR, ensure:
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] No sensitive data (API keys, passwords) in code
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

## 🔄 Pull Request Process

### 1. Update Your Branch

```bash
# Fetch latest changes
git fetch upstream
git rebase upstream/main
```

### 2. Push Your Changes

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to GitHub and create a Pull Request
2. Fill in the PR template with:
   - Description of changes
   - Related issue number (if applicable)
   - Screenshots (for UI changes)
   - Testing performed

### 4. Address Review Comments

- Respond to all review comments
- Make requested changes
- Push updates to the same branch
- Request re-review when ready

### 5. Merge

Once approved, a maintainer will merge your PR.

## 🐛 Reporting Bugs

### Before Reporting

1. Check if the bug has already been reported
2. Verify it's reproducible in the latest version
3. Collect relevant information (logs, screenshots, etc.)

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., macOS, Windows, Linux]
- Browser: [e.g., Chrome, Firefox]
- Version: [e.g., 1.0.0]

**Additional context**
Any other relevant information.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Any other context, mockups, or examples.
```

## 📚 Documentation

### Documentation Guidelines

- Use clear, concise language
- Include code examples where appropriate
- Keep documentation up to date with code changes
- Use proper Markdown formatting
- Add diagrams for complex concepts

### Documentation Structure

```
docs/
├── ARCHITECTURE.md      # System architecture
├── DATA_DICTIONARY.md   # Database schema
├── DEVELOPMENT.md       # Development guide
├── TESTING_GUIDE.md     # Testing instructions
└── TEST_PLAN.md         # Test strategy
```

## 🔐 Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead, email security concerns to: [security@example.com]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Security Best Practices

- Never commit sensitive data (API keys, passwords, tokens)
- Use environment variables for secrets
- Follow OWASP security guidelines
- Keep dependencies up to date
- Use parameterized queries (no SQL injection)
- Validate and sanitize all inputs

## 🎨 UI/UX Guidelines

### Design Principles

- **Simplicity:** Keep interfaces clean and intuitive
- **Consistency:** Use consistent patterns and components
- **Accessibility:** Follow WCAG 2.1 guidelines
- **Responsiveness:** Support all screen sizes
- **Performance:** Optimize for fast load times

### Component Guidelines

- Use existing components from the component library
- Create reusable components for repeated patterns
- Keep components small and focused
- Use TypeScript for type safety
- Add PropTypes or TypeScript interfaces

## 🧪 Testing Guidelines

### Test Coverage

Aim for:
- **Backend:** 80%+ code coverage
- **Frontend:** 70%+ code coverage
- **Critical paths:** 100% coverage

### Test Types

**Unit Tests:**
- Test individual functions/components
- Mock external dependencies
- Fast execution

**Integration Tests:**
- Test component interactions
- Test API endpoints
- Use test database

**E2E Tests:**
- Test complete user flows
- Use real browser (Playwright/Cypress)
- Test critical paths

## 📋 Code Review Guidelines

### For Authors

- Keep PRs small and focused
- Provide context in PR description
- Respond promptly to feedback
- Be open to suggestions

### For Reviewers

- Be respectful and constructive
- Focus on code, not the person
- Explain reasoning for suggestions
- Approve when ready, request changes when needed

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

## 📞 Getting Help

- **GitHub Issues:** For bugs and feature requests
- **GitHub Discussions:** For questions and discussions
- **Documentation:** Check docs/ folder
- **Code Comments:** Read inline documentation

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Barclays Credit Intelligence Platform! 🎉
