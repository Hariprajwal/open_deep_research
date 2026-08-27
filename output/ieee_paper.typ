#import "../templates/ieee_template.typ": ieee

#show: ieee.with(
  title: [Test Paper Title],
  authors: (
    (name: "Author Name", affiliation: "Open Deep Research Engine", email: "researcher@agent.ai"),
  ),
  abstract: [This paper presents a comprehensive research synthesis conducted via multi-agent autonomous deep research.],
  keywords: ("Deep Research", "Multi-Agent System", "Literature Survey", "IEEE Format"),
)

# Test Paper Section
This is test content.
