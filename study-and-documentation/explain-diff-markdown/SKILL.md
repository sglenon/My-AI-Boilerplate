---
name: explain-diff-markdown
description: Create a rich Markdown and Notion explanation of a code change, diff, branch, commit, or pull request. Use when the user wants a beginner-friendly technical walkthrough with background, intuition, grouped code analysis, diagrams, callouts, and a multiple-choice knowledge check published as a Notion page.
---

# Explain a Diff as Markdown

## Investigate the change

1. Identify the exact diff, branch, commit, or pull request in scope. Infer the current branch or working-tree diff when the user does not specify one.
2. Inspect the changed files and enough surrounding code to explain the existing system accurately.
3. Trace relevant data flow, component boundaries, call sites, tests, and user-visible behavior.
4. Distinguish facts found in the code from reasonable inferences. Do not invent behavior that the repository does not support.

## Build the explanation

Create a Markdown-based Notion page with these sections:

### Background

- Explain the broader system relevant to the change.
- Begin with a deep, clearly skippable introduction for readers who are new to the system.
- Narrow gradually to the concepts and components directly affected by the change.

### Intuition

- Explain the essence of the change before its implementation details.
- Use concrete examples and small toy datasets.
- Reuse a small number of diagram families to clarify different cases.
- Include representative example data in diagrams.

### Code

- Walk through the changes at a high level.
- Group and order related edits by concept or execution flow rather than merely following filename order.
- Include focused code excerpts only when they clarify the explanation.
- Call out important definitions, design choices, edge cases, and tradeoffs.

### Quiz

- Write exactly five medium-difficulty multiple-choice questions.
- Test substantive understanding of the change; avoid trivia and gotchas.
- Give each question several plausible options.
- Put each option and its feedback in a Notion toggle block so the reader can reveal whether it is correct.
- Mark feedback with `✅` or `❌` and explain why the option is correct or incorrect.

Use this structure as a guide:

```markdown
1. Question
   ▶ Option 1
     ❌ Explanation of why it is incorrect
   ▶ Option 2
     ✅ Explanation of why it is correct
```

## Format and publish

- Write clear, engaging technical prose with smooth transitions and a classic explanatory flow.
- Use headings, lists, code blocks, diagrams, and callouts supported by Notion.
- Use callouts for key concepts, definitions, and important edge cases.
- Use the available Notion tools to create a new page containing the completed explanation.
- Verify the created page's title, section order, and quiz structure after publishing.
- Return the URL of the new Notion page and briefly identify the diff that was explained.
