# Research Workflow

## Trigger

User asks to research a topic or requests a report. Examples:
- "Research: [topic]"
- "I want a report on [topic]"
- "Can you look into [topic] for me?"

---

## Step 1 — Ask Clarifying Questions (always first, before any research)

Ask the user all five of the following questions in a single message. Adapt the phrasing to fit the topic naturally:

1. **Scope** — How deep do you want this? A quick overview or a thorough deep dive?
2. **Audience** — Who will read this report? What's their background or knowledge level on this topic?
3. **Purpose** — What decision, project, or action will this report support?
4. **Angle** — Is there a specific angle, subtopic, or perspective to focus on? Anything to exclude?
5. **Recency** — Should this focus on the current state of things, or include historical context and how we got here?

Do not begin researching until the user has answered these questions.

---

## Step 2 — Confirm the Research Plan

After the user answers, write a brief research plan (3–5 bullets) summarizing exactly what you will investigate. Ask the user to confirm before proceeding. Example:

> Here's what I'll cover:
> - [angle 1]
> - [angle 2]
> - [angle 3]
> - [data/stats to look for]
> - [sources I'll prioritize]
>
> Good to go?

---

## Step 3 — Research

Once confirmed:
- Run at least 4–6 web searches using different query angles (broad, specific, statistical, recent news, expert opinion, counterargument)
- Prioritize primary sources, government/academic data, reputable publications
- For every key claim or statistic, record the source URL
- Gather enough material to fill all sections of the report template

---

## Step 4 — Organize Findings

Before writing, mentally group all findings into themes that map to the report sections. Identify the 3 strongest subtopics for the Key Findings section.

---

## Step 5 — Write the Report

Use the template at `resources/report-template.md`. Rules:
- Bullet points over paragraphs everywhere possible
- Plain, clear language — no unnecessary jargon
- Every stat or claim in "Data & Evidence" must have a source citation
- Key Takeaways should be genuinely actionable, not vague

---

## Step 6 — Save to output/

- Filename format: `YYYY-MM-DD_topic-slug.md` (e.g., `2026-04-28_index-funds-beginners.md`)
- Create the `output/` directory if it doesn't exist
- Save the complete report as a Markdown file

---

## Step 7 — Show in Chat

- Display the full report in chat
- At the very end, confirm: `Saved to output/YYYY-MM-DD_topic-slug.md`
