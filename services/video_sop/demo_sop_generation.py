#!/usr/bin/env python3
"""
Demo of Video-to-SOP generation workflow
"""

import json
from pathlib import Path
from datetime import datetime

def create_demo_sop():
    """Create a demonstration SOP as if it was generated from a video"""
    
    print("\n" + "="*70)
    print("DEMO: Video-to-SOP Generation (Using 7B VLM)")
    print("="*70)
    
    # Simulated video info
    video_info = {
        "title": "How to Create a New Project in VS Code",
        "duration": 180,  # 3 minutes
        "resolution": "1920x1080",
        "frames_extracted": 18,  # Every 10 seconds
        "audio_transcribed": True
    }
    
    print(f"\n📹 Processing Video: {video_info['title']}")
    print(f"   Duration: {video_info['duration']} seconds")
    print(f"   Resolution: {video_info['resolution']}")
    
    # Simulated processing steps
    print("\n🔄 Processing Steps:")
    print("   1. ✓ Audio extracted using ffmpeg")
    print("   2. ✓ Transcribed with Whisper (speaker detection enabled)")
    print("   3. ✓ Extracted 18 frames at 10-second intervals")
    print("   4. ✓ Analyzed frames with 7B VLM model")
    print("   5. ✓ Correlated transcript with visual actions")
    print("   6. ✓ Generated structured SOP")
    
    # Generate the SOP document
    sop_content = f"""# How to Create a New Project in VS Code

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*Source: Video Tutorial (3:00 duration)*

## Overview
This SOP guides you through creating a new project in Visual Studio Code, including setting up the workspace, initializing version control, and configuring project settings.

## Prerequisites
- [ ] Visual Studio Code installed (version 1.70 or later)
- [ ] Git installed for version control
- [ ] Basic familiarity with command line

## Required Tools
- Visual Studio Code
- Terminal/Command Prompt
- Git

## Steps

### Step 1: Launch Visual Studio Code
*Timestamp: 00:10*

**Instructions:**
Open VS Code by clicking on the application icon or using the command line with `code` command.

**Visual Analysis (7B VLM):**
The screen shows the VS Code welcome page with the activity bar on the left side. The Explorer panel is visible but empty, indicating no folder is currently open.

![Step 1](frames/frame_0001_10s.jpg)

**Tips:**
- 💡 You can also right-click in any folder and select "Open with Code"
- 💡 Use `code .` in terminal to open current directory

---

### Step 2: Open New Window
*Timestamp: 00:20*

**Instructions:**
Click on "File" menu and select "New Window" to start with a fresh workspace.

**Visual Analysis (7B VLM):**
The File menu is expanded showing various options. "New Window" is highlighted, which will create a new VS Code instance. The menu also shows keyboard shortcut Ctrl+Shift+N.

![Step 2](frames/frame_0002_20s.jpg)

**Narration from Audio:**
"Now we'll create a new window to keep our project separate from other work."

---

### Step 3: Create Project Folder
*Timestamp: 00:35*

**Instructions:**
Click "Open Folder" button or use File > Open Folder to create or select your project directory.

**Visual Analysis (7B VLM):**
A file dialog window is open. The user is navigating to the Documents folder. There's a "New Folder" button visible in the dialog toolbar.

![Step 3](frames/frame_0003_35s.jpg)

**Warnings:**
- ⚠️ Choose a location with sufficient disk space
- ⚠️ Avoid using spaces in folder names if possible

---

### Step 4: Name Your Project
*Timestamp: 00:45*

**Instructions:**
Type a descriptive name for your project folder and click "Create".

**Visual Analysis (7B VLM):**
The new folder dialog shows a text input field with "my-new-project" typed in. The naming follows kebab-case convention which is recommended for project directories.

![Step 4](frames/frame_0004_45s.jpg)

**Tips:**
- 💡 Use lowercase and hyphens for better compatibility
- 💡 Keep names concise but descriptive

---

### Step 5: Trust the Authors
*Timestamp: 00:55*

**Instructions:**
When prompted, click "Yes, I trust the authors" if this is your own project folder.

**Visual Analysis (7B VLM):**
A security dialog appears asking about workspace trust. This is VS Code's security feature to prevent malicious code execution. The dialog has options to trust or browse in restricted mode.

![Step 5](frames/frame_0005_55s.jpg)

**Speaker 1 (Instructor):**
"Always review this carefully when opening external projects, but for your own folders, it's safe to trust."

---

### Step 6: Initialize Git Repository
*Timestamp: 01:10*

**Instructions:**
Click on Source Control icon (branch symbol) in the activity bar, then click "Initialize Repository".

**Visual Analysis (7B VLM):**
The Source Control panel is open showing "Initialize Repository" button. The activity bar on the left highlights the Source Control icon. This will create a .git folder in your project.

![Step 6](frames/frame_0006_70s.jpg)

**Tips:**
- 💡 This creates local version control for your project
- 💡 You can also use `git init` in the terminal

---

### Step 7: Create Initial Files
*Timestamp: 01:30*

**Instructions:**
Right-click in Explorer panel and select "New File" to create your first project file.

**Visual Analysis (7B VLM):**
The context menu is open in the Explorer panel with "New File" option highlighted. Other options visible include "New Folder", "Reveal in File Explorer", and "Open in Integrated Terminal".

![Step 7](frames/frame_0007_90s.jpg)

**Common Files to Create:**
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules
- `index.html` or `main.py` - Entry point

---

### Step 8: Configure Settings
*Timestamp: 02:00*

**Instructions:**
Press Ctrl+Shift+P to open command palette and type "settings" to configure project-specific settings.

**Visual Analysis (7B VLM):**
The command palette is open at the top of the window with "settings" typed in the search box. Multiple settings-related commands are shown including "Preferences: Open Settings (JSON)" highlighted.

![Step 8](frames/frame_0008_120s.jpg)

**Recommended Settings:**
- Auto-save
- Format on save
- Tab size
- Line endings

---

### Step 9: Install Extensions
*Timestamp: 02:20*

**Instructions:**
Click Extensions icon in activity bar to browse and install relevant extensions for your project type.

**Visual Analysis (7B VLM):**
The Extensions marketplace is open showing popular extensions. The search bar at the top allows filtering by category or name. Install buttons are visible next to each extension.

![Step 9](frames/frame_0009_140s.jpg)

**Speaker 2 (Assistant):**
"What kind of project are you creating? I can recommend specific extensions."

**Speaker 1 (Instructor):**
"For web development, consider Prettier, ESLint, and Live Server extensions."

---

### Step 10: Save Workspace
*Timestamp: 02:45*

**Instructions:**
Use File > Save Workspace As to save your workspace configuration for easy reopening.

**Visual Analysis (7B VLM):**
The save dialog is open with "my-project.code-workspace" as the filename. This creates a workspace file that remembers your open folders, settings, and debug configurations.

![Step 10](frames/frame_0010_165s.jpg)

**Benefits:**
- Preserves multi-folder setup
- Saves debug configurations
- Remembers workspace-specific settings

---

## Summary

You have successfully created a new VS Code project with:
✅ Dedicated project folder
✅ Git version control initialized
✅ Initial file structure
✅ Configured settings
✅ Relevant extensions installed
✅ Saved workspace configuration

## Quick Reference Commands

| Action | Shortcut | Command |
|--------|----------|---------|
| New Window | Ctrl+Shift+N | File > New Window |
| Open Folder | Ctrl+K Ctrl+O | File > Open Folder |
| Command Palette | Ctrl+Shift+P | View > Command Palette |
| New File | Ctrl+N | File > New File |
| Save Workspace | - | File > Save Workspace As |

## Troubleshooting

**Issue: Git not recognized**
- Solution: Install Git from https://git-scm.com and restart VS Code

**Issue: Extensions not working**
- Solution: Reload window with Ctrl+Shift+P > "Developer: Reload Window"

**Issue: Trust dialog appears repeatedly**
- Solution: Check workspace settings and ensure folder permissions are correct

## Next Steps

1. Create your project structure
2. Set up your development environment
3. Configure debugging if needed
4. Connect to remote repository (GitHub, GitLab, etc.)

## Additional Resources

- [VS Code Documentation](https://code.visualstudio.com/docs)
- [Git Basics](https://git-scm.com/book)
- [Extension Marketplace](https://marketplace.visualstudio.com/vscode)

---

*This SOP was automatically generated from a video tutorial using:*
- *Whisper for transcription with speaker detection*
- *7B VLM model for visual analysis*
- *Automatic step correlation and formatting*
"""
    
    # Save the demo SOP
    output_file = Path("demo_generated_sop.md")
    with open(output_file, 'w') as f:
        f.write(sop_content)
        
    print(f"\n✅ Demo SOP Generated Successfully!")
    print(f"   Saved to: {output_file}")
    
    # Save metadata
    metadata = {
        "title": video_info["title"],
        "source": "demo_video.mp4",
        "duration_seconds": video_info["duration"],
        "frames_extracted": video_info["frames_extracted"],
        "steps_generated": 10,
        "vlm_model": "Qwen2.5-VL-7B",
        "transcription_model": "Whisper",
        "features_used": [
            "Speaker detection",
            "Visual frame analysis",
            "Transcript correlation",
            "Automatic formatting"
        ],
        "generation_time": datetime.now().isoformat()
    }
    
    meta_file = Path("demo_sop_metadata.json")
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"   Metadata: {meta_file}")
    
    print("\n📊 Generation Statistics:")
    print(f"   • Model used: 7B VLM (better accuracy than 3B)")
    print(f"   • Frames analyzed: {video_info['frames_extracted']}")
    print(f"   • Steps generated: 10")
    print(f"   • Processing time: ~2 minutes (simulated)")
    
    print("\n💡 Key Features Demonstrated:")
    print("   • Automatic step detection from video")
    print("   • Visual analysis with 7B VLM model")
    print("   • Speaker detection in transcripts")
    print("   • Correlation of audio and visual content")
    print("   • Professional SOP formatting")
    print("   • Tips and warnings extraction")
    
    print("\n🚀 To use with real videos:")
    print("   1. Ensure VLM service is running (port 8000)")
    print("   2. Ensure Transcription service is running (port 8001)")
    print("   3. Run: python test_video_simple.py <your_video.mp4>")
    
    print("\n" + "="*70)
    

if __name__ == "__main__":
    create_demo_sop()