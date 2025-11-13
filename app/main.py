"""Main FastAPI application for mini-Atlas."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from .agent_loop import agent_loop
from .config import config
from .playwright_runner import playwright_runner
from .schemas import (
    AgentSession, ContinueRequest, RunRequest, RunResponse,
    SessionStatus, StatusResponse
)
from .utils.logging import get_logger
from .templates import dashboard_html, session_detail_html, atlas_interface_html

logger = get_logger(__name__)

# In-memory session storage (replace with Redis/DB in production)
sessions: Dict[str, AgentSession] = {}
session_locks: Dict[str, asyncio.Lock] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting mini-Atlas server...")
    await playwright_runner.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down mini-Atlas server...")
    await playwright_runner.cleanup()


# Create FastAPI app
app = FastAPI(
    title="mini-Atlas",
    description="LLM-powered browser automation agent",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - Dashboard."""
    return dashboard_html()


@app.get("/atlas", response_class=HTMLResponse)
async def atlas_interface():
    """ATLAS-style interface with split view."""
    return atlas_interface_html()


@app.get("/api", response_class=JSONResponse)
async def api_info():
    """API info endpoint."""
    return {
        "name": "mini-Atlas",
        "version": "0.1.0",
        "status": "running",
        "provider": config.settings.llm_provider
    }


@app.get("/session/{session_id}", response_class=HTMLResponse)
async def session_detail_page(session_id: str):
    """Session detail page."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_detail_html()


@app.post("/run", response_model=RunResponse)
async def run_agent(
    request: RunRequest,
    background_tasks: BackgroundTasks
):
    """Start a new agent session."""
    # Generate session ID
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    
    # Create session
    session = AgentSession(
        session_id=session_id,
        url=request.url,
        goals=request.goals,
        profile=request.profile,
        status=SessionStatus.RUNNING
    )
    
    # Store session
    sessions[session_id] = session
    session_locks[session_id] = asyncio.Lock()
    
    # Start agent in background
    background_tasks.add_task(
        run_agent_task,
        session_id,
        request.proxy,
        request.max_steps
    )
    
    logger.info(f"Started session {session_id} with goals: {request.goals}")
    
    return RunResponse(
        session_id=session_id,
        status=SessionStatus.RUNNING
    )


async def run_agent_task(
    session_id: str,
    proxy: Optional[str] = None,
    max_steps: Optional[int] = None
):
    """Background task to run agent."""
    session = sessions.get(session_id)
    if not session:
        logger.error(f"Session {session_id} not found")
        return
    
    async with session_locks[session_id]:
        try:
            # Create browser context
            context = await playwright_runner.create_context(
                session_id,
                proxy=proxy
            )
            
            # Get page
            page = await playwright_runner.get_page(session_id)
            if not page:
                raise Exception("Failed to create page")
            
            # Check if page is still open before applying behavior
            try:
                if not page.is_closed():
                    # Apply stealth and human behavior
                    await playwright_runner.emulate_human_behavior(page)
            except Exception as e:
                logger.warning(f"Could not apply human behavior: {e}")
            
            # Get network monitor
            network_monitor = await playwright_runner.get_network_monitor(session_id)
            
            # Override max steps if specified
            if max_steps:
                original_max = agent_loop.max_steps
                agent_loop.max_steps = max_steps
            
            # Run agent loop
            updated_session = await agent_loop.run(session, page, network_monitor)
            
            # Update stored session
            sessions[session_id] = updated_session
            
            # Restore max steps
            if max_steps:
                agent_loop.max_steps = original_max
            
            logger.info(
                f"Session {session_id} completed with status: {updated_session.status}"
            )
            
        except Exception as e:
            logger.error(f"Agent task failed for session {session_id}: {e}")
            session.status = SessionStatus.FAILED
            sessions[session_id] = session
            
        finally:
            # Cleanup context
            await playwright_runner.close_context(session_id)


@app.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str):
    """Get session status."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get current page info
    page = await playwright_runner.get_page(session_id)
    current_url = page.url if page else session.url
    
    # Get last action
    last_action = None
    if session.steps:
        last_step = session.steps[-1]
        if last_step.action:
            last_action = {
                "action": last_step.action.action.value,
                "timestamp": last_step.timestamp
            }
            
            # Add action-specific details
            if hasattr(last_step.action, "selector"):
                last_action["selector"] = last_step.action.selector
            if hasattr(last_step.action, "value"):
                last_action["value"] = last_step.action.value
    
    # Check for CAPTCHA
    has_captcha = session.status == SessionStatus.WAITING_HUMAN
    
    return StatusResponse(
        session_id=session_id,
        state=session.status,
        current_url=current_url,
        steps_done=session.steps_count,
        last_action=last_action,
        has_captcha=has_captcha,
        error=session.steps[-1].error if session.steps and session.steps[-1].error else None
    )


@app.post("/stop/{session_id}")
async def stop_agent(session_id: str):
    """Stop a running agent."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update status
    session.status = SessionStatus.STOPPED
    sessions[session_id] = session
    
    # Close browser context
    await playwright_runner.close_context(session_id)
    
    logger.info(f"Stopped session {session_id}")
    
    return {"stopped": True, "session_id": session_id}


@app.post("/agent/continue/{session_id}")
async def continue_agent(
    session_id: str,
    request: ContinueRequest,
    background_tasks: BackgroundTasks
):
    """Continue a paused agent session."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != SessionStatus.WAITING_HUMAN:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not waiting for human intervention (status: {session.status})"
        )
    
    # Update status and continue
    session.status = SessionStatus.RUNNING
    sessions[session_id] = session
    
    # Continue in background
    background_tasks.add_task(
        run_agent_task,
        session_id,
        None,  # Use existing proxy
        None   # Use existing max_steps
    )
    
    logger.info(f"Continuing session {session_id} after human intervention")
    
    return {
        "continued": True,
        "session_id": session_id,
        "note": request.note
    }


@app.get("/sessions")
async def list_sessions():
    """List all sessions."""
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "status": s.status.value,
                "goals": s.goals,
                "steps": s.steps_count,
                "created_at": s.created_at.isoformat()
            }
            for s in sessions.values()
        ]
    }


@app.get("/api/session/{session_id}/full")
async def get_session_full(session_id: str):
    """Get full session data including all steps."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get current page info
    page = await playwright_runner.get_page(session_id)
    current_url = page.url if page else session.url
    
    return {
        "session_id": session.session_id,
        "url": session.url,
        "current_url": current_url,
        "goals": session.goals,
        "profile": session.profile.model_dump() if session.profile else None,
        "status": session.status.value,
        "steps": [
            {
                "step_number": step.step_number,
                "observation": {
                    "url": step.observation.url,
                    "title": step.observation.title,
                    "element_count": step.observation.element_count,
                    "has_forms": step.observation.has_forms,
                    "has_buttons": step.observation.has_buttons
                },
                "reasoning": step.reasoning,
                "action": step.action.model_dump() if step.action else None,
                "result": step.result,
                "error": step.error,
                "duration_ms": step.duration_ms,
                "timestamp": step.timestamp.isoformat(),
                "screenshot": step.observation.screenshot  # Base64 encoded
            }
            for step in session.steps
        ],
        "created_at": session.created_at.isoformat(),
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "steps_count": session.steps_count
    }


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Stop if running
    session = sessions[session_id]
    if session.is_active:
        await stop_agent(session_id)
    
    # Remove from storage
    sessions.pop(session_id, None)
    session_locks.pop(session_id, None)
    
    logger.info(f"Deleted session {session_id}")
    
    return {"deleted": True, "session_id": session_id}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if config.settings.log_level == "DEBUG" else None
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "playwright": playwright_runner.browser is not None,
        "sessions_active": sum(1 for s in sessions.values() if s.is_active),
        "sessions_total": len(sessions)
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=config.settings.api_host,
        port=config.settings.api_port,
        reload=config.settings.log_level == "DEBUG",
        log_level=config.settings.log_level.lower()
    )
