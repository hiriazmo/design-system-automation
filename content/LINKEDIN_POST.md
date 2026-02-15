# LinkedIn Post

---

I built a system that audits any website's design system — automatically.

Point it at a URL. It extracts every color, font, spacing value from the DOM. Then 4 AI agents analyze it like a senior design team.

The secret? Not everything needs AI.

Layer 1 (free, <1 second):
- WCAG contrast checker (pure math)
- Type scale detection
- Spacing grid analysis
- Color deduplication

Layer 2 (~$0.003):
- AURORA: identifies brand colors from usage context
- ATLAS: recommends which design system to align with
- SENTINEL: prioritizes fixes by business impact
- NEXUS: synthesizes everything into a final report

My V1 used LLMs for everything.
Cost: ~$1/run. Accuracy: mediocre (LLMs hallucinate math).

V2 flipped the approach:
Deterministic code handles certainty. LLMs handle ambiguity.

Result: 100-300x cheaper. More accurate. Always produces output even when LLMs fail.

The rule engine does 80% of the work for $0.
The agents handle the 20% that requires judgment.

Built with: Playwright + HuggingFace Inference API (Qwen 72B, Llama 3.3 70B) + Gradio + Docker

Full write-up on Medium (link in comments).

What design workflows are you automating? Would love to hear.

#UXDesign #AIEngineering #DesignSystems #HuggingFace #LLM #Accessibility #WCAG #MultiAgent #Gradio #BuildInPublic
