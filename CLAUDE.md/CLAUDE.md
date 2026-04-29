# Project Context

This is my AI agent workspace. I use it for research, content creation, and productivity workflows.

# About Me

I create content about financial literacy, business knowledge and funding, and stock exchange leveraging and best practices for my investment group's business. My audience are historically minorities and people who are just leaving college, think practically, and want fun, entertaining ways to learn about money through trends, tutorials, and well-planned, curated events that develop a community of like-minded people. I prefer clear, concise output of high-value.

# Rules

- Always ask clarifying questions before starting a complex task
- Show your plan and steps before executing
- Keep reports and summaries concise (bullet points over paragraphs)
- Save all output files to the output folder
- Cite sources when doing research

# Research Workflow

When the user asks to research a topic or requests a report, follow the recipe in `workflows/research-workflow.md`. Always ask clarifying questions before starting any research. Save all reports to `output/` and display them in full in chat after saving. Use `resources/report-template.md` as the report structure.

# Project Structure

- workflows/ - Workflow instruction files (plain English recipes the agent follows)
- output/ - Finished deliverables (reports, drafts, analysis)
- resources/ - Reference docs and templates