# Contributing to Docling v2

Thank you for your interest in contributing to Docling v2! We welcome contributions from the community and are grateful for your help in improving this project.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:
- Be respectful and inclusive
- Exercise consideration and respect in your speech and actions
- Attempt collaboration before conflict
- Refrain from demeaning, discriminatory, or harassing behavior

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

1. **Use a clear and descriptive title**
2. **Describe the exact steps to reproduce the problem**
3. **Provide specific examples to demonstrate the steps**
4. **Describe the behavior you observed after following the steps**
5. **Explain which behavior you expected to see instead and why**
6. **Include screenshots and animated GIFs if possible**
7. **Include your environment details (OS, Python version, Node.js version, etc.)**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

1. **Use a clear and descriptive title**
2. **Provide a step-by-step description of the suggested enhancement**
3. **Provide specific examples to demonstrate the steps or current behavior**
4. **Describe the current behavior and explain which behavior you expected to see**
5. **Explain why this enhancement would be useful to most Docling v2 users**

### Pull Requests

1. **Fork the repository**
2. **Create a new branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Run tests and ensure code quality**
5. **Commit your changes** (`git commit -m 'Add some amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Git

### Local Development

1. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/docling_v2.git
   cd docling_v2
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start development servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

## Code Quality Standards

### Backend (Python)
- Use **Black** for code formatting
- Use **Flake8** for linting
- Use **mypy** for type checking
- Write comprehensive tests with **pytest**
- Follow PEP 8 style guide

### Frontend (TypeScript/React)
- Use **ESLint** for code quality
- Use **Prettier** for code formatting
- Write comprehensive tests
- Follow React best practices

### Testing
- Write tests for new features
- Ensure all tests pass before submitting PR
- Include both unit tests and integration tests where appropriate

### Documentation
- Update README.md when adding new features
- Add comments for complex logic
- Update API documentation if endpoints change

## Commit Message Guidelines

We use conventional commit messages:

```
feat: add new document processing endpoint
fix: resolve memory leak in document upload
docs: update API documentation
style: format code with black
refactor: improve document chunking logic
test: add tests for authentication
chore: update dependencies
```

## Review Process

1. **Initial review** - Maintainers will review your PR within 3-5 business days
2. **Feedback** - You may receive feedback or requested changes
3. **Approval** - Once approved, your PR will be merged
4. **Deployment** - Changes will be included in the next release

## Questions?

If you have any questions about contributing, please:
- Check the [README.md](README.md)
- Open an issue for discussion
- Contact the maintainers

Thank you for contributing to Docling v2! 🚀