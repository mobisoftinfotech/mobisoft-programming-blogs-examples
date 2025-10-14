# MCP Code Reviewer

Automated code review MCP server with technology-specific checklists and real-time progress tracking.

## Features

-  **Auto-detect technology stack** from project files
-  **Technology-specific checklists** for Python, JavaScript/TypeScript, and Java
-  **Real-time progress tracking** with pass/fail/skip counts
-  **Comprehensive checks** covering:
  - Security vulnerabilities
  - Code quality issues
  - Performance problems
  - Best practices
  - Testing coverage
-  **Detailed reporting** with file locations and line numbers
-  **Severity levels** (critical, warning, info)

## Installation

### Prerequisites

- Python 3.11 or higher
- `uv` package manager (recommended) or `pip`

### Setup

1. **Navigate to the project directory:**
   ```bash
   cd mcp-code-reviewer
   ```

2. **Install dependencies:**
   ```bash
   # Using uv (recommended)
   uv sync 
   
   #or 
   uv pip install -e .

   # Or using pip
   pip install -e .
   ```

3. **Configure in Claude Desktop:**

   Edit your Claude Desktop config file:
   - **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

   Add the MCP server for windows:
   ```json
   {
     "mcpServers": {
      "mcp-code-reviewer": {
        "command": "uv",
        "args": [
          "--directory",
          "C:\\Users\\YourUsername\\code\\mcp-code-reviewer",
          "run",
          "mcp-code-reviewer"
        ],
        "env": {
          "DANGEROUSLY_OMIT_AUTH": "true"
        }
      }
    }
   }
   ```
   Add the MCP server for windows:
   ```json
   {
     "mcpServers": {
      "mcp-code-reviewer": {
        "command": "uv",
        "args": [
          "--directory",
          "/Users/yourname/code/mcp-code-reviewer",
          "run",
          "mcp-code-reviewer"
        ],
        "env": {
          "DANGEROUSLY_OMIT_AUTH": "true"
        }
      }
     }
    }
   ```

4. **Restart Claude Desktop, End from task manager**

## Usage

### In Claude Desktop

Once configured, the tools are automatically available. Just chat with Claude:

**Example 1: Quick Review**
```
You: "Review my Python project at /Users/me/my-app"

Claude will:
1. Detect technology (Python)
2. Load Python checklist
3. Execute all checks with real-time progress
4. Show results with pass/fail counts
```

**Example 2: Check Specific Technology**
```
You: "What checks are on the JavaScript checklist?"

Claude will show all JavaScript/React checks organized by category
```

**Example 3: Get Available Checklists**
```
You: "What technologies can you review?"

Claude will list: python, javascript, java, etc.
```

### Available MCP Tools

#### 1. `detect_tech(project_path)`
Detects technology stack from project files.

**Example:**
```python
detect_tech("/path/to/project")
```

**Returns:**
```json
{
  "primary": "python",
  "frameworks": ["django", "flask"],
  "confidence": 0.9
}
```

#### 2. `get_available_checklists()`
Lists all available technology checklists.

**Example:**
```python
get_available_checklists()
```

**Returns:**
```json
{
  "available_checklists": ["python", "javascript", "java"],
  "count": 3
}
```

#### 3. `get_checklist(technology)`
Shows all checks for a specific technology.

**Example:**
```python
get_checklist("python")
```

**Returns:** Complete checklist with all categories and checks

#### 4. `review_code(project_path, technology=None)`
Executes comprehensive code review with real-time progress.

**Example:**
```python
review_code("/path/to/project", technology="python")
# or auto-detect:
review_code("/path/to/project")
```

**Returns:**
```json
{
  "technology": "python",
  "summary": {
    "total_checks": 25,
    "passed": 18,
    "failed": 5,
    "skipped": 2,
    "percentage": 80.0
  },
  "failures": [
    {
      "check_id": "SEC-001",
      "message": "Hardcoded API key found",
      "file_path": "config.py",
      "line_number": 12,
      "severity": "critical"
    }
  ],
  "status_text": "✅ 18 passed | ❌ 5 failed | ⏭️ 2 skipped"
}
```

#### 5. `get_review_status(project_path, technology=None)`
Gets status of a previously run review.

## Supported Technologies

### Python
- **Frameworks**: Django, Flask, FastAPI
- **Categories**: Security, Code Quality, Performance, Best Practices, Testing
- **Total Checks**: 20+

**Key Checks:**
- Hardcoded credentials detection
- SQL injection prevention
- Dangerous function usage (eval, exec)
- PEP 8 compliance
- Type hints and docstrings

### JavaScript/TypeScript
- **Frameworks**: React, Vue, Node.js, Angular
- **Categories**: Security, Code Quality, Performance, Best Practices, React-specific
- **Total Checks**: 25+

**Key Checks:**
- XSS vulnerabilities
- console.log in production
- React optimization (memo, keys)
- Modern syntax (const/let vs var)
- ESLint configuration

### Java
- **Frameworks**: Spring Boot, Maven, Gradle
- **Categories**: Security, Code Quality, Performance, Best Practices, Spring-specific
- **Total Checks**: 20+

**Key Checks:**
- SQL injection (PreparedStatement)
- Exception handling
- Resource management (try-with-resources)
- SOLID principles
- Spring dependency injection

## Customization

### Adding Custom Checklists

Create a new YAML file in `checklists/` directory:

```yaml
technology: rust
description: Code review checklist for Rust projects

categories:
  - name: Security
    items:
      - id: SEC-001
        description: No unsafe blocks without justification
        validator: check_unsafe_usage
        severity: warning
        patterns:
          - 'unsafe\s*\{'
```

### Checklist Structure

```yaml
technology: <name>
description: <description>

categories:
  - name: <category_name>
    items:
      - id: <CHECK-ID>
        description: <what to check>
        validator: <validator_function>
        severity: critical|warning|info
        patterns:  # regex patterns (optional)
          - '<pattern1>'
          - '<pattern2>'
        files:  # specific files to check (optional)
          - 'filename.ext'
```

## Architecture

```
mcp-code-reviewer/
├── main.py                  # MCP server entry point
├── technology_detector.py   # Auto-detect tech stack
├── checklist_engine.py      # Execute reviews
├── checklists/              # YAML checklist files
│   ├── python.yaml
│   ├── javascript.yaml
│   └── java.yaml
├── validators/              # Validation logic
│   ├── base_validator.py
│   ├── pattern_validator.py
│   └── file_validator.py
└── reporters/               # Progress tracking
    └── progress_tracker.py
```

## Progress Tracking

The server provides real-time updates as checks execute:

```
Progress: [████████████░░░░░░░░] 60% (15/25)
✅ 12 passed | ❌ 3 failed | ⏭️ 0 skipped

Current: SEC-003 - Checking for dangerous function usage...
```

## Severity Levels

- 🔴 **Critical**: Security vulnerabilities, must fix immediately
- 🟡 **Warning**: Important issues, should fix soon
- 🔵 **Info**: Suggestions for improvement
- ⚠️ **Error**: Tool execution errors

## Troubleshooting

### "Could not detect technology"
- Ensure project has indicator files (package.json, requirements.txt, etc.)
- Manually specify technology: `review_code(path, technology="python")`

### "Checklist not found"
- Check available checklists: `get_available_checklists()`
- Verify checklist file exists in `checklists/` directory

### "Project path does not exist"
- Use absolute paths, not relative
- Verify path on your system

## Roadmap

- [ ] Add more languages (Go, Rust, C#, PHP)
- [ ] Custom rule engine
- [ ] Integration with CI/CD
- [ ] VSCode extension
- [ ] HTML report generation
- [ ] Fix suggestions with AI
- [ ] Performance profiling

## Contributing

1. Add new checklist YAML files for additional technologies
2. Extend validators for custom check types
3. Improve detection accuracy
4. Add framework-specific checks

## License

MIT License

## Author

Created by Mobisoft Infotech Pvt Ltd
