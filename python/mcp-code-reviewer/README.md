# MCP Code Reviewer

An MCP server that reviews code with YAML checklists. Claude Desktop (or any MCP client) can call its five tools to detect a project's technology, load a checklist, and run a review.

This is the example code for the two-part Mobisoft Infotech blog series:

- Part 1: [AI Agent Development Example with Custom MCP Server: Build a Code Review Agent](https://mobisoftinfotech.com/resources/blog/ai-development/ai-agent-development-custom-mcp-server-code-review)
- Part 2: [AI Agent Development with MCP Server: Integration, Testing & Deployment](https://mobisoftinfotech.com/resources/blog/ai-development/ai-agent-development-mcp-server-integration-deployment)

`main.py` matches Part 2. It is a standalone, simplified server built on version 2 of the MCP Python SDK, and it does not import the Part 1 modules.

## Requirements

- Python 3.10 or higher (tested on Python 3.13)
- [uv](https://docs.astral.sh/uv/)
- Node.js, only if you want to use the MCP Inspector

The pinned versions are `mcp[cli]==2.3.0` and `pyyaml==6.0.3`. In SDK version 2, the server class is `MCPServer` (`from mcp.server.mcpserver import Context, MCPServer`). The old `mcp.server.fastmcp` import no longer works. If you need SDK version 1, pin `mcp<2` and use the FastMCP import instead. Do not mix the two.

## Setup

```bash
cd mcp-code-reviewer
uv sync
```

`uv sync` creates `.venv` and installs the `mcp-code-reviewer` command defined in `pyproject.toml`.

## Tools

| Tool | Input | What it does |
| --- | --- | --- |
| `detect_tech` | `project_path`: a config file such as `package.json`, `pyproject.toml`, `requirements.txt` or `pom.xml` | Maps the file name to a technology |
| `get_available_checklists` | none | Lists the YAML files in `checklists/` |
| `get_checklist` | `name`, such as `javascript` | Returns one checklist |
| `review_code` | `project_path`: a project folder | Runs the regex checks on `.js`, `.py` and `.java` files, with progress updates and a time limit |
| `get_review_status` | `review_id` | Returns the status of a review from this server session |

Every error comes back as short JSON, for example `{"error": "Unknown checklist: ruby"}`.

Sample `review_code` result for a project with one `eval()` call:

```json
{
  "review_id": "ab733df9",
  "status": "completed",
  "files": 1,
  "skipped": 0,
  "truncated": false,
  "findings": [
    {
      "file": "app.js",
      "check": "SEC-002"
    }
  ]
}
```

## Safety limits

- **Approved folders only.** The tools read only inside the folders listed in `REVIEW_ALLOWED_DIRS`. Without it, they read only the folder the server starts in. Symlinks are resolved before the check. Separate several folders with `;` on Windows and `:` on macOS and Linux.
- **Skipped files.** The review skips symlinks, secret files (`.env`, `id_rsa`, `id_ed25519`, `*.pem`, `*.key`, `*.p12`), files over 200 KB, unreadable files, and the `node_modules`, `.git`, `.venv`, `venv`, `__pycache__` and `dist` folders.
- **Bounded scans.** A review stops after 500 files or 20 seconds and reports `truncated` or `stopped (time limit)`.
- **Demo-only state.** Review status lives in memory. It disappears when the server restarts, and separate processes do not share it.

## Configure Claude Desktop

Claude Desktop is available for macOS, Windows, and Linux (beta). Open the config file from Settings → Developer → Edit Config, or edit it directly:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

macOS and Linux:

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
        "REVIEW_ALLOWED_DIRS": "/Users/yourname/code/projects"
      }
    }
  }
}
```

Windows:

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
        "REVIEW_ALLOWED_DIRS": "C:\\Users\\YourUsername\\code\\projects"
      }
    }
  }
}
```

Use absolute paths. If Claude Desktop cannot find `uv`, put the full path to `uv` in `command`. Quit Claude Desktop completely and start it again, then check that the server shows as running under Settings → Developer.

Example prompts:

- "Can you detect what technology is used in my project? The config file is at /path/to/project/package.json"
- "What code review checklists do you have available?"
- "Show me what checks are included in the JavaScript checklist."
- "Please review my project at /path/to/project"

## Test with the MCP Inspector

```bash
uv run mcp dev main.py
```

The command starts the Inspector with `npx` and prints a local address that includes an access token. Open it, switch on the server connection, open the Tools tab, pick a tool, enter its arguments, and choose Execute Tool. The Messages panel shows each request and response.

Keep the Inspector bound to localhost and keep its token private. Never turn off its authentication.

## Checklists

Checklists live in `checklists/` and use this structure:

```yaml
technology: python
description: Code review checklist for Python projects

categories:
  - name: Security
    items:
      - id: SEC-003
        description: No eval() or exec() usage
        validator: check_dangerous_functions
        severity: critical
        patterns:
          - "\\beval\\("
          - "\\bexec\\("
```

`review_code` reads every `patterns` entry as a Python regular expression and reports the item's `id` when a file matches. Items with `validator: check_test_files` hold file-name globs such as `*.test.js`, so `review_code` skips them.

Quote every pattern. In single quotes, backslashes stay literal (`'\beval\('`). In double quotes, double them (`"\\beval\\("`). An unquoted pattern that starts with `[` is read as a YAML list.

To add a language, add a checklist such as `checklists/ruby.yaml`, then add its config file to `CONFIG_FILES` and its source suffix to `SOURCE_SUFFIXES` in `main.py`.

## Troubleshooting

- **Request timed out (-32001) on `detect_tech`:** pass a config file, not a folder.
- **`ModuleNotFoundError`:** delete `.venv`, run `uv sync`, and restart Claude Desktop.
- **`failed to remove file .venv/lib64: Access is denied`:** the `.venv` was created in WSL. Delete it and let the Windows side recreate it.
- **Server will not start:** check the Claude Desktop logs (macOS `~/Library/Logs/Claude/`, Windows `%APPDATA%\Claude\logs\`, Linux `~/.config/Claude/logs/`), then run `uv run mcp-code-reviewer` in the project folder and read the output.

## Project layout

```
mcp-code-reviewer/
├── main.py                  # Part 2: the MCP server (SDK v2)
├── pyproject.toml
├── checklists/              # YAML checklists used by main.py
│   ├── python.yaml
│   ├── javascript.yaml
│   └── java.yaml
├── technology_detector.py   # Part 1 components, kept for reference.
├── checklist_engine.py      #   main.py does not import them.
├── validators/
├── reporters/
└── test_tools.py            # Exercises the Part 1 components
```

## Production use

This server is a local demonstration. Before you deploy an MCP server for a team, add authentication and authorization, monitoring, persistent job state, secret storage, and tests for failures, restarts and concurrent calls. Part 2 of the blog series has the full checklist.

## License

MIT License

## Author

Created by Mobisoft Infotech Pvt Ltd
