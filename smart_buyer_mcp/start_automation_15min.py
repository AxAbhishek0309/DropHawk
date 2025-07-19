#!/usr/bin/env python3
"""
Smart Buyer MCP - Automated Deal Hunter (15-minute intervals)
Runs every 15 minutes to find and track deals automatically
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.scheduler import DealScheduler

def main():
    print("🚀 Starting Smart Buyer MCP Automation (15-min intervals)...")
    print("⏰ Will run every 15 minutes")
    print("📱 Sending updates to Telegram")
    print("🗑️ Auto-removing expired deals")
    print("💰 Comprehensive price tracking")
    print("📊 Monitoring 5 websites: Amazon, Flipkart, Myntra, Nykaa, Ajio")
    print("🎯 NO SAMPLE DATA - Only real live deals!")
    print("\nPress Ctrl+C to stop")
    
    try:
        scheduler = DealScheduler()
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        print("\n🛑 Stopping Smart Buyer MCP...")
        print("✅ Automation stopped safely")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 