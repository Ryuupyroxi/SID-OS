#!/usr/bin/env python3
"""SID Model Downloader - CLI tool for downloading AI models.
Usage: python3 download_model.py <model_name>"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if len(sys.argv) < 2:
    print("Usage: download_model.py <model_name>")
    print("Example: download_model.py 'Qwen2.5-3B-Instruct'")
    sys.exit(1)

model_name = sys.argv[1]

# Initialize model manager
from ai.engine.model_manager import ModelManager

# Create minimal config
class MinConfig:
    ram_tier = os.environ.get('SID_RAM_TIER', '4gb')
    context_window = 4096
    api_key = ""
    api_endpoint = ""

mm = ModelManager(MinConfig())

# Find and download the model
success = mm.download_model(model_name)
if success:
    print(f"\n✓ Model '{model_name}' downloaded successfully")
    print(f"  Path: /sid/models/")
    print(f"  Run 'sid' to start using it")
else:
    print(f"\n✗ Failed to download '{model_name}'")
    print(f"  Available models:")
    for cat_name, models in mm.KNOWN_MODELS.items():
        for m in models:
            if m.url:
                print(f"    - {m.name}")
    sys.exit(1)
