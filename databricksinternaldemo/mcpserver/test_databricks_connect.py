#!/usr/bin/env python3
"""Test script to verify Databricks Connect is properly configured.

This script tests the Databricks Connect setup by:
1. Loading environment variables from .databricks/.databricks.env
2. Creating a Spark session
3. Running a simple query to verify connectivity
"""

import os
import sys
from pathlib import Path


def load_databricks_env():
    """Load environment variables from .databricks/.databricks.env file."""
    env_file = Path(__file__).parent / ".databricks" / ".databricks.env"
    
    if not env_file.exists():
        print(f"⚠️  Warning: {env_file} not found")
        return False
    
    print(f"📄 Loading environment from {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value
                print(f"   ✓ {key}")
    
    return True


def test_connection():
    """Test Databricks Connect connection."""
    try:
        from databricks.connect import DatabricksSession
        
        print("\n🔌 Creating Spark session...")
        spark = DatabricksSession.builder.getOrCreate()
        
        print(f"✅ Spark session created successfully!")
        print(f"   Spark version: {spark.version}")
        print(f"   Cluster ID: {os.environ.get('DATABRICKS_CLUSTER_ID', 'N/A')}")
        print(f"   Host: {os.environ.get('DATABRICKS_HOST', 'N/A')}")
        
        print("\n🧪 Running test query...")
        result = spark.sql("SELECT 1 as test_value, current_timestamp() as timestamp")
        result.show()
        
        print("\n✅ Databricks Connect is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error connecting to Databricks: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're authenticated: databricks configure")
        print("2. Verify your cluster is running")
        print("3. Check that DATABRICKS_CLUSTER_ID is set correctly")
        return False


if __name__ == "__main__":
    print("🚀 Testing Databricks Connect Configuration\n")
    
    # Load environment variables
    if not load_databricks_env():
        print("⚠️  Continuing without .databricks.env file...")
    
    # Test connection
    success = test_connection()
    
    sys.exit(0 if success else 1)







