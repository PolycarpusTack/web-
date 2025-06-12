import httpx
import asyncio
import json

async def debug_backend():
    async with httpx.AsyncClient() as client:
        print("=== Testing Backend API ===")
        
        # 1. Test if backend is running
        try:
            response = await client.get("http://localhost:8002/docs")
            print(f"Backend docs endpoint: {response.status_code}")
        except Exception as e:
            print(f"Backend not accessible: {e}")
            return
            
        # 2. Test models endpoint with detailed error
        try:
            response = await client.get("http://localhost:8002/api/models/available")
            print(f"\nModels endpoint status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Response headers: {dict(response.headers)}")
                print(f"Response body: {response.text}")
                
                # Try to parse error detail
                try:
                    error_detail = response.json()
                    print(f"Error detail: {json.dumps(error_detail, indent=2)}")
                except:
                    pass
                    
        except Exception as e:
            print(f"Error calling models endpoint: {e}")
            
        # 3. Test with authentication
        headers = {"X-API-Key": "dev_key_123"}
        try:
            response = await client.get("http://localhost:8002/api/models/available", headers=headers)
            print(f"\nWith auth - status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Found {len(data.get('models', []))} models")
            else:
                print(f"Auth failed: {response.text}")
        except Exception as e:
            print(f"Error with auth: {e}")

asyncio.run(debug_backend())
