---
name: web-research
description: Comprehensive web research workflow with strategic planning, source evaluation, and synthesis guidance
---

# Web Research Skill

This skill provides a structured approach to conducting web research using Claude's web search capabilities. It guides the research process from initial planning through information gathering, critical evaluation, and synthesis.

## When to Use This Skill

Use this skill when you need to:
- Research complex topics requiring multiple information sources
- Gather current information from the web with strategic planning
- Evaluate and synthesize information from diverse sources
- Produce well-sourced summaries or reports
- Balance thoroughness with efficiency in information gathering

## Research Process

The web research skill follows a four-step process:

### 1. Plan First

Before starting your search, think strategically about:
- **Query complexity**: Is this a simple factual question or a complex topic requiring multiple perspectives?
- **Source value**: What types of sources would be most authoritative and useful?
- **Tool budget**: How many tool calls will you likely need? (2-5 for simple queries, 10-15 for complex topics)
- **Stopping conditions**: How will you know when you have sufficient information?

### 2. Search Strategically

Conduct searches with a clear strategy:
- **Start broad**: Begin with general searches to understand the landscape and identify key concepts
- **Then narrow**: Follow up with specific searches for details, evidence, or particular perspectives
- **Stop appropriately**: Avoid over-searching once you have enough quality information to answer the question
- **Iterate thoughtfully**: Let early results inform subsequent searches

### 3. Evaluate Critically

Not all search results are equally valuable:
- **Assess source authority**: Prioritize authoritative, well-established sources for factual information
- **Check for bias**: Consider the perspective and potential biases of each source
- **Verify claims**: Note when information may need independent verification
- **Consider recency**: For time-sensitive topics, prioritize recent information
- **Cross-reference**: Look for corroboration across multiple sources

### 4. Synthesize Clearly

Present findings in an organized, useful format:
- **Organize logically**: Structure information in a way that's easy to understand
- **Cite sources**: Always reference where information came from
- **Acknowledge uncertainty**: Be transparent about limitations or conflicting information
- **Provide context**: Help users understand the significance of findings
- **Balance detail**: Include enough depth without overwhelming with irrelevant information

## Stopping Conditions

It's okay to stop searching when:
- You've found sufficient high-quality information to answer the question
- Additional searches are unlikely to add significant value
- You've reached a reasonable tool call budget for the query complexity
- Diminishing returns set in (new searches repeat information already found)

**Remember**: Perfect is the enemy of good. Aim for helpful, accurate information rather than exhaustive perfection.

## Best Practices

- **Budget awareness**: Simple queries typically need 2-5 searches; complex topics may need 10-15
- **Quality over quantity**: Five high-quality sources are better than twenty mediocre ones
- **User needs first**: Focus on information that directly addresses the user's question
- **Iterative refinement**: Use early search results to refine your search strategy
- **Save important findings**: Use the memory tool to preserve key information before context limits are reached

## Integration with Other Tools

This skill works well with:
- **Memory tool**: Save research findings to `./memories` for later reference
- **Text editor**: Create structured reports or documents from research findings
- **Bash tool**: Process or analyze data discovered during research

## Dependencies

- Web search tool (server-side, automatically available)
- No additional packages required

## Notes

- This skill provides guidance for effective research workflows
- It does not include executable scripts (prompt-based only)
- The skill emphasizes strategic thinking and quality over exhaustive searching
- Designed to balance thoroughness with efficiency and token budget constraints
