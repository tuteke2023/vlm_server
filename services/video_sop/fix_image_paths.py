#!/usr/bin/env python3
"""
Fix image paths in the intelligent SOP to handle spaces properly
"""

import urllib.parse

# Read the current SOP
with open("intelligent_ato_sop.md", "r") as f:
    content = f.read()

# The actual filenames with spaces
filenames = [
    "smart_frame_0000_28.0s_go to.jpg",
    "smart_frame_0001_35.0s_go to.jpg", 
    "smart_frame_0002_41.6s_scene_change.jpg",
    "smart_frame_0003_45.0s_see.jpg",
    "smart_frame_0004_55.0s_available.jpg",
    "smart_frame_0005_60.0s_select.jpg",
    "smart_frame_0006_65.0s_see.jpg",
    "smart_frame_0007_70.0s_download.jpg"
]

# URL encode the filenames for markdown
for filename in filenames:
    # Find variations of how it might appear in the markdown
    variations = [
        f"intelligent_frames/{filename}",
        f"intelligent_frames/{filename.replace(' ', '_')}",  # If underscores were used
        f"intelligent_frames/{filename.replace(' ', '')}",    # If spaces were removed
    ]
    
    # Correct path with URL encoding for spaces
    encoded_filename = filename.replace(' ', '%20')
    correct_path = f"intelligent_frames/{encoded_filename}"
    
    for variant in variations:
        if variant in content:
            content = content.replace(variant, correct_path)
            print(f"Fixed: {variant} -> {correct_path}")

# Write the fixed content
with open("intelligent_ato_sop_fixed.md", "w") as f:
    f.write(content)

print("\n✅ Fixed SOP saved to: intelligent_ato_sop_fixed.md")
print("The image paths now properly handle spaces with %20 encoding")