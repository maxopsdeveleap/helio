# Hellio HR - Claude Code Work Rules

## Project Context
Hellio HR is an intelligent hiring operations assistant built as part of Develeap's Agenteer Boot Camp. The system helps manage candidates and job positions while keeping humans in control of hiring decisions.

## Code Style & Standards

### JavaScript
- Use modern ES6+ syntax (const/let, arrow functions, template literals)
- Use async/await for asynchronous operations
- Prefer functional programming patterns where appropriate
- Add comments only for complex logic, not obvious code
- Use descriptive variable names (no single letters except loop counters)

### Python (for backend in future exercises)
- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Use FastAPI best practices (dependency injection, Pydantic models)
- Organize code: routes, services, models, utils

### File Organization
```
hellio-hr-max/
├── .claude/          # Claude Code configuration
├── data/             # JSON data files (candidates, positions)
├── public/           # Frontend (HTML, CSS, JS)
├── src/              # Backend source (future exercises)
└── tests/            # Test files (future exercises)
```

## Git Commit Guidelines
- Use present tense ("Add feature" not "Added feature")
- First line: concise summary (50 chars max)
- Body: bullet points for multiple changes
- No emojis or "Claude Code" attribution (as per user preference)
- Example:
  ```
  Add candidate filtering by skills

  - Implement skill-based search
  - Update UI to show filter controls
  - Add tests for filter logic
  ```

## Development Workflow

### Before Making Changes
1. Read existing code to understand patterns
2. Check for similar implementations in codebase
3. Ask user for clarification if requirements are ambiguous

### When Writing Code
- Prefer editing existing files over creating new ones
- Keep solutions simple - avoid over-engineering
- Don't add features not explicitly requested
- Test changes in browser before committing

### Error Handling
- Always wrap fetch calls in try-catch
- Show user-friendly error messages
- Log errors to console for debugging
- Fail gracefully - don't break the whole app

## Tool Usage Preferences

### File Operations
- Use Read before Edit or Write
- Use Glob for finding files by pattern
- Use Grep for searching file contents
- Avoid bash cat/grep when dedicated tools exist

### Sub-Agents
- Use for complex multi-step tasks (5+ steps)
- Use for tasks requiring multiple file searches
- Don't use for simple single-file operations
- Prefer parallel agent execution when tasks are independent

### Testing
- Always test in browser after frontend changes
- Run python3 -m http.server 8000 to serve locally
- Open http://localhost:8000/public/index.html
- Check browser console for errors

## Project-Specific Rules

### Data Extraction
- Manual extraction from CVs using AI (not automated parsing)
- Keep JSON structure consistent across all candidates/positions
- Include all relevant fields even if some are null

### UI/UX
- Professional, clean design
- Responsive layout (mobile-friendly)
- Clear visual hierarchy
- Accessible (keyboard navigation, ARIA labels)

### Performance
- Lazy load large datasets
- Minimize API calls
- Cache data when appropriate
- Use efficient search/filter algorithms

## Bootcamp Context
- Current exercise: Exercise 1 (Days 1-2) - COMPLETE
- Next exercise: Exercise 2 (Days 3-4) - Backend with FastAPI
- Learning objectives: claude.md, custom commands, MCP tools, sub-agents
- Repository: https://github.com/maxopsdeveleap/helio

## User Preferences
- User: Max (Junior DevOps at Develeap)
- Prefers concise commit messages without attribution
- Wants to verify each step
- Learning to use AI tools effectively
- F5 doesn't work (brightness control) - use Ctrl+R to refresh browser
