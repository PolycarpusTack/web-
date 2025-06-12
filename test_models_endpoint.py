import httpx
import asyncio

async def test_models_endpoint():
    async with httpx.AsyncClient() as client:
        try:
            # Test direct Ollama connection
            ollama_response = await client.get("http://localhost:11434/api/tags")
            print(f"Direct Ollama response: {ollama_response.status_code}")
            
            # Test backend API endpoint
            api_response = await client.get("http://localhost:8002/api/models/available")
            print(f"Backend API response: {api_response.status_code}")
            
            if api_response.status_code != 200:
                print(f"Error response: {api_response.text}")
                
                # Try with headers
                headers = {"X-API-Key": "dev_key_123"}
                api_response2 = await client.get("http://localhost:8002/api/models/available", headers=headers)
                print(f"Backend API with auth response: {api_response2.status_code}")
                
                if api_response2.status_code != 200:
                    print(f"Error with auth: {api_response2.text}")
            else:
                print(f"Success: {api_response.json()}")
                
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test_models_endpoint())
