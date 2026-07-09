---
name: explain-diff-html
description: Create a rich, interactive, self-contained HTML explanation of a code change, diff, branch, commit, or pull request. Use when the user wants a visual technical walkthrough with beginner-friendly background, intuition, code-change analysis, diagrams, and an interactive quiz.
---

# Explain a Diff as HTML

## Investigate the change

1. Identify the exact diff, branch, commit, or pull request in scope. Infer the current branch or working-tree diff when the user does not specify one.
2. Inspect the changed files and enough surrounding code to explain the existing system accurately.
3. Trace relevant data flow, component boundaries, call sites, tests, and user-visible behavior.
4. Distinguish facts found in the code from reasonable inferences. Do not invent behavior that the repository does not support.

## Build the explanation

Create one long page with a table of contents and these sections:

### Background

- Explain the broader system relevant to the change.
- Begin with a deep, clearly skippable introduction for readers who are new to the system.
- Narrow gradually to the concepts and components directly affected by the change.

### Intuition

- Explain the essence of the change before its implementation details.
- Use concrete examples and small toy datasets.
- Reuse a small number of visual diagram families throughout the page.
- Use simplified UI diagrams for user-interface changes.
- Use system diagrams for data flow or communication between components, including representative example data.

### Code

- Walk through the changes at a high level.
- Group and order related edits by concept or execution flow rather than merely following filename order.
- Include focused code excerpts only when they clarify the explanation.
- Call out important definitions, design choices, edge cases, and tradeoffs.

### Quiz

- Write exactly five medium-difficulty multiple-choice questions.
- Test substantive understanding of the change; avoid trivia and gotchas.
- Make every option clickable with JavaScript.
- After a click, show whether the answer is correct and explain why.

## Write the HTML

- Produce a single self-contained HTML file with inline CSS and JavaScript and no required external assets.
- Use a responsive, single-page layout with section headings and a table of contents. Do not use tabs for top-level navigation.
- Write clear, engaging technical prose with smooth transitions and a classic explanatory flow.
- Use styled HTML elements for diagrams and HTML list elements for lists. Never use ASCII diagrams.
- Use callouts for key concepts, definitions, and important edge cases.
- Use `<pre>` elements for code blocks. If a styled `div` is unavoidable, give it `white-space: pre-wrap`.
- Before saving, inspect every code block and confirm that its effective CSS uses `white-space: pre` or `white-space: pre-wrap`.
- Ensure quiz interactions work without a server.

## Save and report

- Save the file outside the repository in a global temporary location.
- Prefix the filename with today's local date in `YYYY-MM-DD-` format and add a concise slug, for example `/tmp/2026-01-12-explanation-auth-refresh.html`.
- Return a clickable link to the generated file and briefly identify the diff that was explained.
