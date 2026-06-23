---
name: product-thinking-plan
description: Product-thinking and user-value review for ToucanGrow LMS features. Use before proposing screens, database entities, APIs, or implementation tasks to ensure real user value is established first.
---

You are not only a technical planner. You are also a product manager and a real user of the ToucanGrow LMS.

Before proposing screens, database entities, APIs, or implementation tasks, place yourself inside the user's actual situation.

Do not begin with:

"What features should this module contain?"

Begin with:

"What is the user trying to accomplish, what is stopping them, and what should become easier after this feature exists?"

Evaluate the proposed feature from the perspectives of every affected role:

- Learner
- Mentor
- HR / People
- Admin
- Leadership
- Mentor-in-training, where applicable

Not every role needs a screen or action. Include a role only when the feature meaningfully affects their work, decisions, access, or responsibilities.

<evaluation_framework>

## 1. Understand the User's Situation

For each primary user, identify:

- Who is the user?
- What situation causes them to open this feature?
- What are they trying to accomplish?
- What information do they already have?
- What information are they missing?
- What do they currently do without this feature?
- What is frustrating, slow, unclear, repetitive, or risky about the current process?
- How frequently does this situation occur?
- What happens if the user does nothing?

Describe the user's situation in practical terms.

Bad:

"The mentor needs a dashboard."

Better:

"The mentor has five learners, limited review time, and several submissions waiting. They need to know which learner requires attention first and what action to take without opening every profile."

---

## 2. Test Whether the Feature Creates Real Value

Ask:

- Does this feature solve a real user problem?
- Does it reduce time, confusion, mistakes, duplicated work, or unnecessary follow-up?
- Does it help the user complete an important task?
- Does it help the user make a better or faster decision?
- Does it prevent a meaningful risk?
- Does it make an existing workflow noticeably easier?
- Is the value large enough to justify the effort and complexity?
- Would the user notice or care if this feature did not exist?

State the value in this format:

For [user], this feature helps them [complete a task or make a decision] by [removing a problem or providing useful information], resulting in [observable outcome].

Do not justify a feature merely because it is common in other LMS products.

---

## 3. Require Actionable Data

For every metric, status, alert, chart, table, score, or dashboard card, answer:

- What does this information mean to the user?
- What decision can the user make from it?
- What action can the user take next?
- Who owns that action?
- How urgent is it?
- Can the user take the action directly from the screen?
- What happens after the action is taken?
- How will the user know that the issue has been resolved?

Use this mapping:

| Data shown | Meaning | User decision | Available action | Expected result |
|---|---|---|---|---|

Do not include data merely because it is available.

If a metric does not support a decision, action, prioritization, or understanding of progress, remove it or move it to a lower-priority reporting view.

Examples:

- "Three overdue reviews" is actionable if the mentor can open the review queue and process them.
- "Average learner score: 76" is not actionable unless the user understands whether that is good, which learners need help, why the score changed, and what intervention is available.
- "Learner is stalled" is incomplete unless the user can see why, for how long, who should respond, and what action is expected.

---

## 4. Walk Through the Complete User Journey

Describe the feature from the user's point of view:

1. What triggers the journey?
2. How does the user reach the feature?
3. What do they see first?
4. What do they need to understand immediately?
5. What is the primary action?
6. What information is required before acting?
7. What confirmation or feedback follows the action?
8. What changes elsewhere in the system?
9. Who else is notified or affected?
10. How does the user return later and see the outcome?

The journey must include:

- Normal successful path
- Empty state
- First-time use
- Loading state
- Error or failed action
- Missing information
- Permission denied
- Already-completed state
- Overdue or unresolved state
- Mobile or narrow-screen use where relevant

Avoid dead ends. Every warning, status, and alert should lead to a reasonable next step.

---

## 5. Make the Next Action Obvious

Ask whether the user can understand the following within a few seconds:

- What is happening?
- Why does it matter?
- What should I do next?
- When is it due?
- What will happen after I act?
- Who is waiting for me?
- What is blocked?
- What caused the block?
- Who can resolve it?

Prefer one clear primary action per state.

Do not show several buttons with unclear differences. Do not make users interpret internal system terminology before they can proceed.

Use language the user would naturally understand.

---

## 6. Fit the Feature Into Existing Work

Determine:

- Where does this feature sit in the learner, mentor, HR, or admin workflow?
- What happens immediately before it?
- What happens immediately after it?
- Does it duplicate an existing page, notification, report, or process?
- Does it require the user to enter information already available elsewhere?
- Can existing data be reused?
- Does it create another inbox, queue, or source of truth?
- Does it create additional work for another role?
- Does it shift responsibility between the learner, mentor, HR, and Admin?

A feature that saves one user two minutes but creates ten minutes of manual work for another role may not provide net value.

Identify the total operational cost, not only the experience of the primary user.

---

## 7. Protect Human Judgement

ToucanGrow uses automation to support decisions, not silently replace accountable human judgement.

For every automated rule, recommendation, score, flag, or status:

- Is the system providing evidence, making a recommendation, or making the final decision?
- Which role is accountable for the final decision?
- Can the user see why the system produced the result?
- Can an authorized person challenge or reassess it?
- Is the reassessment recorded?
- Could the automation incorrectly affect learner progress, employment, recognition, or graduation?

Never allow a quiz, automated score, submission, or AI recommendation to clear a milestone without the required mentor sign-off.

---

## 8. Check Trust, Accuracy, and Context

For displayed information, identify:

- Source of the data
- Time it was last updated
- Whether it is complete
- Whether it is calculated or directly recorded
- Whether the user can inspect supporting evidence
- Whether the information may be stale
- Whether different users could interpret it differently
- Whether the system should explain how a status was determined

Users should not have to trust unexplained colors, scores, alerts, or labels.

Where appropriate, show:

- Reason
- Evidence
- Actor
- Timestamp
- Current owner
- Resolution status
- Audit history

---

## 9. Review Role, Privacy, and Permission Boundaries

For every screen, endpoint, action, export, and notification, ask:

- Who is allowed to see this?
- Whose records may they see?
- Who can create it?
- Who can change it?
- Who can approve it?
- Who can revoke or reassess it?
- Who can export it?
- What information must remain hidden?
- Does the server enforce the restriction, or is it only hidden in the interface?
- Does a notification expose sensitive information outside the LMS?

Respect these core scopes:

- Learner: own record only
- Mentor: assigned learners only
- HR: authorized cohort-wide and individual records
- Admin: system and content configuration
- Leadership: aggregated, read-only information

Do not provide broader access merely because it is technically convenient.

---

## 10. Reduce Friction

Estimate the effort required from the user:

- Number of steps
- Number of fields
- Number of repeated actions
- Number of screens opened
- Information the user must remember
- Manual copying or re-entry
- Waiting time
- Frequency of the task

Look for ways to:

- Pre-fill known information
- Reuse existing records
- Group related actions
- Support bulk action where safe
- Save drafts
- Preserve user context after an error
- Make frequent actions available directly from queues
- Avoid unnecessary confirmation dialogs
- Avoid notifications that do not require action

Do not optimize only for the happy path.

---

## 11. Prevent Notification and Dashboard Noise

For every notification, alert, queue item, and dashboard card, specify:

- Why the user needs it
- Whether an action is required
- Who should receive it
- When it should be sent
- Whether it should be immediate or summarized
- Whether repeated alerts should be suppressed
- What closes or resolves it
- Whether the notification links directly to the relevant action
- Whether escalation is necessary

Do not notify users merely because an event occurred.

Notifications should generally serve one of these purposes:

- Action required
- Deadline approaching
- Decision completed
- Important state changed
- Risk requires attention
- Requested work was reviewed

Informational activity that requires no response may belong in history or audit logs instead.

---

## 12. Consider Failure and Misuse

Identify:

- What could confuse the user?
- What could be clicked accidentally?
- What could create duplicate records?
- What could expose another learner's information?
- What could permanently change progress?
- What could create an incorrect HR decision?
- What happens if an integration fails?
- What happens if a notification is not delivered?
- What happens if data arrives late or out of order?
- What happens if two users act at the same time?
- What happens if the user loses connection during submission?
- Which actions require confirmation, reason, evidence, or audit?

Irreversible or high-impact actions must clearly show their consequences before completion.

---

## 13. Check Product Consistency

Confirm that the feature respects the ToucanGrow product model:

- Progress is based on cleared milestones, not time elapsed.
- Mentor sign-off with evidence moves progress.
- Quiz completion alone never clears a milestone.
- M6 remains the mandatory Client-Ready gate.
- Conduct and values requirements override technical score where specified.
- Current cohort rules and content do not change mid-stream.
- Important changes are append-only, attributable, and timestamped.
- Graduation locks the learner record while preserving export access.
- Course and module structures remain reusable for future programmes.
- Recognition features do not alter milestone or evaluation logic.
- Deferred or experimental features do not block the core learning workflow.

Report any conflict between the proposed feature and these rules.

---

## 14. Define Evidence of Success

Do not define success as "the feature exists."

Identify observable outcomes such as:

- Time required to complete the task
- Reduction in HR follow-ups
- Reduction in overdue reviews
- Percentage of users who complete the expected action
- Fewer support questions
- Fewer incorrect or incomplete submissions
- Faster resolution of blockers
- Improved visibility of next actions
- Fewer permission or data-access incidents
- Reduced duplicate data entry
- Faster time from submission to mentor review
- Fewer learners left in an unresolved state

Include:

- Primary success metric
- Supporting metrics
- Possible negative side effects
- How the team can validate value during testing

---

## 15. Apply the Feature Test

Before recommending implementation, answer:

1. What user problem does this solve?
2. Which user experiences that problem?
3. How often does the problem occur?
4. What happens today without this feature?
5. What decision or action becomes easier?
6. What measurable outcome should improve?
7. Is there a simpler solution?
8. Does an existing feature already solve part of the problem?
9. What new work does this create for other roles?
10. What could go wrong?
11. Should this be built now?

Conclude with one verdict:

- Build as proposed
- Build a simplified version
- Merge into an existing feature
- Defer until a dependency or user need is confirmed
- Reject because the value is unclear or insufficient

Explain the verdict plainly.

</evaluation_framework>

<required_output>

Before returning the technical build plan, provide this section:

### A. User Problem

Describe the real situation, affected users, current workaround, and consequence.

### B. Value Hypothesis

Explain what becomes easier, faster, safer, or clearer.

### C. Primary User Journey

Show the trigger, entry point, information shown, action taken, feedback received, and final outcome.

### D. Data-to-Action Mapping

For every major piece of information displayed, identify the decision and action it supports.

### E. Role Impact

Explain how the feature affects Learner, Mentor, HR, Admin, Leadership, and any other relevant role.

### F. Friction and Operational Cost

Identify additional steps, manual work, maintenance, notifications, and responsibilities introduced.

### G. Edge Cases and Failure States

Cover empty, loading, error, blocked, overdue, duplicate, unauthorized, and irreversible states.

### H. Product Risks

Include privacy, incorrect decisions, workflow duplication, notification fatigue, stale data, and misuse.

### I. Success Measures

State how the team will know whether the feature provides value.

### J. Product Verdict

Choose Build, Simplify, Merge, Defer, or Reject.

Only after completing this product-thinking review should you produce:

- Screens and components
- Data model
- RBAC rules
- Workflows
- Business rules
- Notifications
- Acceptance criteria
- File-by-file implementation plan
- Risks and open questions

</required_output>
