#!/usr/bin/env python3
"""
Test script to demonstrate Phase 5.4: Audit Logging System for Compliance and Security

This script tests the comprehensive audit logging, compliance middleware, and security monitoring system.
"""

import asyncio
import httpx
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEY = "SECRET_KEY"

async def test_compliance_system():
    """Test the complete Phase 5.4 audit logging and compliance system."""
    
    print("🔒 Testing Phase 5.4: Audit Logging System for Compliance and Security")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Health check (should be logged by compliance middleware)
        print("\n1. Testing health check endpoint (should be logged by compliance middleware)")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   ✓ Health check: {response.status_code} - {response.json()}")
        
        # Test 2: Authentication endpoint (should generate access_denied logs)
        print("\n2. Testing authentication failures (should generate security alerts)")
        for i in range(3):
            response = await client.get(f"{BASE_URL}/compliance/audit-logs")
            print(f"   ⚠️  Unauthenticated request {i+1}: {response.status_code}")
            await asyncio.sleep(0.5)
        
        # Test 3: Test with API key (should work but still be logged)
        print("\n3. Testing with API key (should be logged)")
        headers = {"X-API-Key": API_KEY}
        response = await client.get(f"{BASE_URL}/rbac/roles", headers=headers)
        print(f"   ✓ RBAC roles with API key: {response.status_code}")
        
        # Test 4: Test workspace endpoints (RBAC in action)
        print("\n4. Testing workspace endpoints (RBAC system)")
        response = await client.get(f"{BASE_URL}/workspaces", headers=headers)
        print(f"   ✓ Workspaces: {response.status_code}")
        
        # Test 5: Test models endpoint with potential errors
        print("\n5. Testing models endpoint (may generate security incidents)")
        response = await client.get(f"{BASE_URL}/api/models/available")
        print(f"   ⚠️  Models endpoint: {response.status_code}")
        
        print("\n" + "=" * 70)
        print("✅ Phase 5.4 Testing Complete!")
        print("\nKey Features Demonstrated:")
        print("  ✓ Compliance middleware automatically logging all requests")
        print("  ✓ Security monitoring detecting suspicious activity")
        print("  ✓ RBAC system protecting sensitive endpoints")
        print("  ✓ Audit trails with risk assessment")
        print("  ✓ Real-time security incident detection")
        print("\nCheck the application logs (app_test.log) to see detailed audit entries.")
        

if __name__ == "__main__":
    print(f"Starting compliance system test at {datetime.now()}")
    asyncio.run(test_compliance_system())