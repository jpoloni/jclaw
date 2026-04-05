"""Core orchestrator - processes messages through agents."""

import time
from typing import Any

from jclaw.core.agent_registry import AgentRegistry
from jclaw.core.context_window import ContextWindowManager
from jclaw.core.handoff import HandoffRouter
from jclaw.guardrails import GuardrailRegistry
from jclaw.llm import LLMRouter, TokenCounter
from jclaw.memory import SessionMemory
from jclaw.observability import log_llm_call, log_llm_response, set_trace_id
from jclaw.prompts import PromptContext, PromptEngine
from jclaw.skills import SkillExecutor
from jclaw.types import (
    AgentNotFoundError,
    GuardrailBlockedError,
    InboundMessage,
    Message,
    OutboundMessage,
)


class Orchestrator:
    """Core orchestrator - 12-step message processing loop."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        memory: SessionMemory,
        llm_router: LLMRouter,
        skill_executor: SkillExecutor,
        prompt_engine: PromptEngine,
        guardrail_registry: GuardrailRegistry,
        token_counter: TokenCounter,
        handoff_router: HandoffRouter | None = None,
    ):
        """Initialize orchestrator."""
        self.agent_registry = agent_registry
        self.memory = memory
        self.llm_router = llm_router
        self.skill_executor = skill_executor
        self.prompt_engine = prompt_engine
        self.guardrail_registry = guardrail_registry
        self.token_counter = token_counter
        self.handoff_router = handoff_router or HandoffRouter()
        self.max_tool_iterations = 10

    async def process(self, inbound: InboundMessage) -> OutboundMessage:
        """Process a message through the 12-step loop.

        Steps:
        1. Acquire lock
        2. Load session, get active agent
        3. Input guardrails
        4. Render prompt
        5. Build context with token budget
        6. Tool loop: LLM call + skill execution
        7. Output guardrails
        8. Persist messages
        9. Send response
        10. Release lock
        """
        set_trace_id(inbound.message_id)
        start_time = time.time()

        # Step 1-2: Get session & agent
        session_id = f"{inbound.channel}:{inbound.chat_id}"
        await self.memory.set_metadata(session_id, "last_message_id", inbound.message_id)

        # Get active agent (default to first)
        active_agent_id = await self.memory.get_metadata(session_id, "active_agent_id")
        if not active_agent_id:
            first_agent = self.agent_registry.get_first_agent()
            if not first_agent:
                return OutboundMessage(text="No agents configured")
            active_agent_id = first_agent.agent_id

        try:
            agent_config = self.agent_registry.get_agent(active_agent_id)
        except AgentNotFoundError:
            return OutboundMessage(text=f"Agent '{active_agent_id}' not found")

        # Step 3: Input guardrails
        input_pipeline = self.guardrail_registry.build_input_pipeline(agent_config.guardrails)
        from jclaw.guardrails import GuardrailContext

        gr_context = GuardrailContext(
            session_id=session_id,
            agent_id=active_agent_id,
            user_id=inbound.user_id,
            channel=inbound.channel,
        )
        input_result = await input_pipeline.check_input(inbound.text or "", gr_context)

        if input_result.action == "block":
            return OutboundMessage(
                text=input_result.reason or "Your message was blocked"
            )

        # Create user message
        user_message = Message(
            role="user",
            content=input_result.modified_content or inbound.text or "",
            metadata={"channel": inbound.channel, "user_id": inbound.user_id},
        )

        # Step 4: Get conversation history
        history = await self.memory.get_messages(session_id, limit=50)
        all_messages = history + [user_message]

        # Step 5: Render prompt
        prompt = await self.prompt_engine.render(
            agent_config,
            PromptContext(
                session_id=session_id,
                agent_id=active_agent_id,
                channel=inbound.channel,
                user_id=inbound.user_id,
            ),
        )

        # Step 6: Tool loop
        tools = self.skill_executor.skill_registry.get_tools_for_agent(agent_config)
        cwm = ContextWindowManager(agent_config, self.token_counter)
        payload = cwm.build_payload(prompt.content, all_messages, tools)

        response_text = ""
        tool_iterations = 0

        while tool_iterations < self.max_tool_iterations:
            tool_iterations += 1

            # Call LLM
            log_llm_call(
                model=agent_config.llm_model,
                provider=agent_config.llm_provider,
                input_tokens=payload.input_tokens,
            )

            llm_response = await self.llm_router.complete(
                messages=payload.messages,
                provider_id=agent_config.llm_provider,
                model=agent_config.llm_model,
                temperature=agent_config.temperature,
                max_tokens=agent_config.max_tokens,
                tools=payload.tools if tools else None,
            )

            log_llm_response(
                model=agent_config.llm_model,
                provider=agent_config.llm_provider,
                output_tokens=llm_response.usage.output_tokens,
                latency_ms=llm_response.latency_ms,
                stop_reason=llm_response.stop_reason,
            )

            response_text = llm_response.content or ""

            # If no tools were called, we're done
            if llm_response.stop_reason != "tool_use" or not llm_response.tool_calls:
                break

            # Execute tools
            from jclaw.skills import SkillContext

            skill_context = SkillContext(
                session_id=session_id,
                agent_config=agent_config,
                inbound_message=inbound,
                metadata={},
            )

            tool_results, handoff_request = await self.skill_executor.execute_all(
                llm_response.tool_calls,
                skill_context,
            )

            # Check for handoff
            if handoff_request:
                target_agent = self.agent_registry.get_agent(
                    handoff_request.target_agent_id
                )
                await self.handoff_router.execute(
                    handoff_request,
                    self.memory,
                    agent_config,
                    target_agent,
                )
                # Recursively process with new agent
                await self.memory.set_metadata(
                    session_id,
                    "active_agent_id",
                    handoff_request.target_agent_id,
                )
                # Continue with new agent
                active_agent_id = handoff_request.target_agent_id
                agent_config = target_agent
                break

            # Add tool results to messages
            for tool_result in tool_results:
                payload.messages.append(
                    Message(
                        role="tool",
                        content=str(tool_result.output),
                        tool_call_id=tool_result.tool_call_id,
                    )
                )

        # Step 7: Output guardrails
        output_pipeline = self.guardrail_registry.build_output_pipeline(
            agent_config.guardrails
        )
        output_result = await output_pipeline.check_output(response_text, gr_context)

        if output_result.action == "block":
            response_text = output_result.reason or "Response blocked"

        # Step 8: Persist messages
        await self.memory.add_message(session_id, user_message)
        await self.memory.add_message(
            session_id,
            Message(
                role="assistant",
                content=response_text,
                metadata={"agent_id": active_agent_id},
            ),
        )

        latency_ms = (time.time() - start_time) * 1000

        # Step 9: Return response
        return OutboundMessage(text=response_text)
