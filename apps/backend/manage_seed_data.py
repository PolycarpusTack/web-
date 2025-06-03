#!/usr/bin/env python3
"""
Seed Data Management CLI for Web+ Backend
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    parser = argparse.ArgumentParser(description="Manage seed data for Web+ backend")
    parser.add_argument(
        "environment",
        choices=["development", "testing", "staging", "production"],
        help="Target environment"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force seed even if data exists"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be seeded without actually doing it"
    )
    
    args = parser.parse_args()
    
    print(f"🏎️ Ferrari Seed Data Manager")
    print(f"Environment: {args.environment}")
    print(f"Force: {args.force}")
    print(f"Dry Run: {args.dry_run}")
    print("=" * 50)
    
    if args.dry_run:
        print("DRY RUN - No actual changes will be made")
        # Show what would be seeded
        from db.seed_data import SeedDataManager
        seeder = SeedDataManager(args.environment)
        
        print("\\nUsers that would be created:")
        users = seeder._get_users_data()
        for user in users:
            print(f"  - {user['username']} ({user['role']})")
        
        print("\\nModels that would be created:")
        models = seeder._get_models_data()
        for model in models:
            print(f"  - {model['id']} ({model['provider']})")
        
        if args.environment == "development":
            pipelines = seeder._get_pipelines_data()
            print(f"\\nPipelines that would be created: {len(pipelines)}")
            for pipeline in pipelines:
                print(f"  - {pipeline['name']}")
        
        return
    
    try:
        from db.seed_data import seed_database
        
        print("Starting seed process...")
        results = await seed_database(args.environment, args.force)
        
        print("\\n" + "=" * 50)
        print("🏎️ FERRARI SEED RESULTS")
        print("=" * 50)
        
        if results.get("success", False):
            print("✅ Seed process completed successfully!")
            
            for category, data in results.get("results", {}).items():
                if isinstance(data, dict) and "created" in data:
                    print(f"\\n{category.title()}:")
                    print(f"  Created: {data['created']}")
                    
                    if data.get(category):
                        for item in data[category][:3]:  # Show first 3
                            print(f"    - {item}")
                        if len(data[category]) > 3:
                            print(f"    ... and {len(data[category]) - 3} more")
            
            print(f"\\n🏁 Ferrari is ready to race in {args.environment}!")
            
        else:
            print("❌ Seed process failed!")
            if "error" in results:
                print(f"Error: {results['error']}")
            
        # Save results to file
        results_file = Path(f"seed_results_{args.environment}.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\\n📄 Results saved to: {results_file}")
        
        return results.get("success", False)
        
    except Exception as e:
        print(f"❌ Seed management failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)