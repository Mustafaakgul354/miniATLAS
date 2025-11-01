"""Basic usage example for mini-Atlas API."""

import asyncio
import httpx
import json
from typing import Optional


class MiniAtlasClient:
    """Simple client for mini-Atlas API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def run_agent(self, url: str, goals: list, profile: Optional[dict] = None):
        """Start a new agent session."""
        data = {
            "url": url,
            "goals": goals,
            "session_mode": "ephemeral"
        }
        if profile:
            data["profile"] = profile
        
        response = await self.client.post(f"{self.base_url}/run", json=data)
        response.raise_for_status()
        return response.json()
    
    async def get_status(self, session_id: str):
        """Get session status."""
        response = await self.client.get(f"{self.base_url}/status/{session_id}")
        response.raise_for_status()
        return response.json()
    
    async def wait_for_completion(self, session_id: str, poll_interval: int = 2):
        """Wait for session to complete."""
        while True:
            status = await self.get_status(session_id)
            print(f"Status: {status['state']}, Steps: {status['steps_done']}")
            
            if status['state'] in ('completed', 'failed', 'stopped'):
                return status
            
            if status['state'] == 'waiting_human':
                print("CAPTCHA detected! Please solve it manually and continue...")
                # In a real app, you'd handle this appropriately
                return status
            
            await asyncio.sleep(poll_interval)
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()


async def example_search():
    """Example: Search for something on a website."""
    client = MiniAtlasClient()
    
    try:
        # Start agent
        print("Starting search agent...")
        result = await client.run_agent(
            url="https://www.example.com",
            goals=[
                "Search for 'python programming'",
                "Click on the first result"
            ]
        )
        
        session_id = result['session_id']
        print(f"Session started: {session_id}")
        
        # Wait for completion
        final_status = await client.wait_for_completion(session_id)
        print(f"\nFinal status: {json.dumps(final_status, indent=2)}")
        
    finally:
        await client.close()


async def example_login():
    """Example: Login to a website."""
    client = MiniAtlasClient()
    
    try:
        # Start agent with profile
        print("Starting login agent...")
        result = await client.run_agent(
            url="https://example.com/login",
            goals=[
                "Login to the website",
                "Navigate to user dashboard",
                "Find account settings"
            ],
            profile={
                "email": "test@example.com",
                "password": "test123"
            }
        )
        
        session_id = result['session_id']
        print(f"Session started: {session_id}")
        
        # Monitor progress
        final_status = await client.wait_for_completion(session_id)
        
        if final_status['state'] == 'completed':
            print("\nSuccessfully completed all goals!")
        else:
            print(f"\nSession ended with status: {final_status['state']}")
            if final_status.get('error'):
                print(f"Error: {final_status['error']}")
        
    finally:
        await client.close()


async def example_form_filling():
    """Example: Fill out a contact form."""
    client = MiniAtlasClient()
    
    try:
        print("Starting form filling agent...")
        result = await client.run_agent(
            url="https://example.com/contact",
            goals=[
                "Fill out the contact form with test information",
                "Submit the form",
                "Verify submission was successful"
            ],
            profile={
                "name": "John Doe",
                "email": "john@example.com",
                "message": "This is a test message from mini-Atlas"
            }
        )
        
        session_id = result['session_id']
        print(f"Session started: {session_id}")
        
        # Wait and show progress
        while True:
            status = await client.get_status(session_id)
            
            if status.get('last_action'):
                action = status['last_action']
                print(f"Step {status['steps_done']}: {action['action']} "
                      f"{action.get('selector', '')}")
            
            if status['state'] in ('completed', 'failed', 'stopped'):
                break
            
            await asyncio.sleep(1)
        
        print(f"\nFinal state: {status['state']}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    # Run examples
    print("mini-Atlas Usage Examples\n" + "="*40 + "\n")
    
    # Uncomment the example you want to run:
    
    # asyncio.run(example_search())
    # asyncio.run(example_login())
    asyncio.run(example_form_filling())