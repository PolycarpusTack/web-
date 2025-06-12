"""
Debug script to call the models endpoint with full error details
"""
import httpx
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "backend"))

async def debug_models_endpoint():
    async with httpx.AsyncClient() as client:
        # Call the endpoint and capture full response
        try:
            response = await client.get(
                "http://localhost:8002/api/models/available",
                follow_redirects=True,
                timeout=30.0
            )
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Body: {response.text}")
            
            # If there's a JSON response, pretty print it
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    import json
                    data = response.json()
                    print("\nJSON Response:")
                    print(json.dumps(data, indent=2))
                except:
                    pass
                    
        except Exception as e:
            print(f"Request failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_models_endpoint())
