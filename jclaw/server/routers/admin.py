"""Admin and health check endpoints."""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "jclaw",
    }


@router.get("/agents")
async def list_agents(request: Request):
    """List all registered agents."""
    agent_registry = request.app.state.agent_registry
    agents = agent_registry.list_agents()

    return {
        "agents": [
            {
                "id": agent.agent_id,
                "name": agent.name,
                "description": agent.description,
                "model": agent.llm_model,
                "skills": agent.skills,
            }
            for agent in agents
        ],
        "count": len(agents),
    }


@router.get("/agents/{agent_id}")
async def inspect_agent(agent_id: str, request: Request):
    """Inspect agent details."""
    agent_registry = request.app.state.agent_registry

    try:
        agent = agent_registry.get_agent(agent_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "description": agent.description,
        "llm_provider": agent.llm_provider,
        "llm_model": agent.llm_model,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
        "context_window": agent.context_window,
        "skills": agent.skills,
        "handoff_targets": agent.handoff_targets,
    }


@router.get("/sessions")
async def list_sessions(request: Request):
    """List active sessions."""
    memory = request.app.state.memory
    sessions = await memory.get_active_sessions()

    return {
        "sessions": sessions,
        "count": len(sessions),
    }
