# Agent Delegation Rule

Whenever you receive a task or prompt, you **MUST** immediately create and delegate the work to specialized subagents. Do not attempt to complete complex tasks entirely on your own in the main thread. 

## Guidelines:
1. **Subagent Creation**: Analyze the prompt and create one or more subagents using the `invoke_subagent` tool (and `define_subagent` if a custom role is needed).
2. **Model Selection**: Assign the most suitable model for each subagent based on its specific role:
   - Use **`pro`** for complex logic, backend modifications, security audits, and deep debugging.
   - Use **`flash`** or **`flash_lite`** for frontend tweaks, simple research, reading files, and quick verifications.
3. **Roles**: Clearly define roles such as "Backend Developer", "Frontend Developer", "Security Auditor", or "Bug Checker" depending on the prompt's requirements.
4. **Monitoring**: After spawning subagents, you must keep watch on them. Use the `schedule` tool to set check-in timers (`TimerCondition="any"`) if waiting for long tasks, or simply await their messages. Synthesize their results to complete the user's request.
