# LangChain vs Raw OpenAI API

## Decision
Use raw OpenAI API for Phase 1.

## Reasoning
- Simpler architecture
- Lower abstraction overhead
- Easier debugging
- Full control over prompts and JSON responses
- Current workflow is deterministic and does not require complex agents

## Future Consideration
LangChain may be evaluated later for:
- multi-step reasoning
- memory
- autonomous workflows
- tool orchestration