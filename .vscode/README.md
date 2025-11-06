# VS Code Configuration

This directory contains VS Code workspace settings that ensure consistent formatting and linting across the project.

## Setup Instructions

1. **Install Recommended Extensions**: When you open this workspace, VS Code will prompt you to install the recommended extensions listed in `extensions.json`. Click "Install All" to set up your environment.

2. **Python Interpreter**: Make sure to select the virtual environment interpreter:
   - Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
   - Select "Python: Select Interpreter"
   - Choose `./venv/bin/python3`

3. **Automatic Formatting**: The workspace is configured to:
   - Format Python files with Black on save
   - Apply Ruff fixes automatically on save
   - Format TypeScript/JavaScript with Prettier
   - Run ESLint fixes for the frontend

## Key Extensions

### Required for Python Development
- **Python** (`ms-python.python`): Core Python support
- **Ruff** (`charliermarsh.ruff`): Fast Python linter (formatting disabled)

### Required for Next.js Frontend
- **TypeScript Importer** (`pmneo.tsimporter`): Auto-import TypeScript symbols
- **Prettier** (`esbenp.prettier-vscode`): Code formatting for JS/TS
- **ESLint** (`dbaeumer.vscode-eslint`): JavaScript/TypeScript linting
- **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`): Tailwind CSS support

### Recommended for Development
- **GitLens** (`eamodio.gitlens`): Enhanced Git capabilities
- **Test Adapter Converter** (`ms-vscode.test-adapter-converter`): Test runner integration

## Why This Setup?

The VS Code configuration ensures that:
- **Pre-commit hooks are authoritative**: All formatting and fixing is handled by pre-commit hooks
- **Consistent code style**: All team members produce identical formatting via pre-commit
- **No commit rejections**: Pre-commit hooks ensure code passes CI/CD pipeline standards
- **VS Code shows same linting**: You see the exact same errors pre-commit would catch
- **Clean development workflow**: Focus on coding, let pre-commit handle quality

## Development Workflow

1. **Write code** in VS Code - you'll see the same linting errors as pre-commit
2. **Format and fix code** using pre-commit hooks:
   ```bash
   pre-commit run --all-files  # Format and fix all files
   # or
   git commit  # Triggers formatting and fixing automatically
   ```
3. **VS Code shows linting errors** in real-time, matching pre-commit exactly

## Key Principles

- **Pre-commit is the single source of truth** for code quality
- **VS Code formatting matches Black** used in pre-commit
- **VS Code linting matches Ruff** configuration used in pre-commit
- **No auto-formatting on save** - pre-commit handles all formatting
- **All fixes happen via pre-commit** - not VS Code auto-fixes

## Troubleshooting

If pre-commit hooks aren't working:
1. Install pre-commit: `pip install pre-commit`
2. Install hooks: `pre-commit install`
3. Run manually: `pre-commit run --all-files`

If VS Code linting doesn't match pre-commit:
1. Check that Ruff extension is installed and using `pyproject.toml` config
2. Verify Python interpreter is set to `./venv/bin/python3`
3. Reload VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window")

If you want to format a single file manually:
```bash
black src/some_file.py
ruff check --fix src/some_file.py
```

If pre-commit hooks still fail after formatting:
- The issue might be in uncommitted files
- Run `make format` locally to ensure everything is formatted
- Check for any manual formatting overrides in your VS Code user settings
