# ATO Report Retrieval - VLM-Verified Visuals

## Overview
This SOP was created using real visual AI (Qwen2.5-VL-7B) to verify that frames actually match the narration.
No shortcuts - each frame was analyzed by the VLM to confirm it shows what's being described.

## Steps with AI-Verified Visuals

### Step 1: You go to the ATO portal

**Narration Time:** 28.0s  
**Visual Actually Appears:** 38.0s (+10.0s delay)  
**VLM Analysis:** Yes, the image shows the ATO (Australian Taxation Office) portal homepage. The layout includes sections for "My practice," "Reports and forms," and "Communication." It also displays information such a  
**Confidence:** 90%

![Step 1](vlm_analyzed_frames/matched_38.0s_the_ATO_portal_dashboard_or_ho.jpg)

---

### Step 2: You go to the reports

**Narration Time:** 35.0s  
**Visual Actually Appears:** 37.0s (+2.0s delay)  
**VLM Analysis:** Yes, the image shows a "Reports" section or menu. The interface includes a button labeled "Reports" among other options such as "Add client," "View client list," "Remove client," and "Loggment program  
**Confidence:** 90%

![Step 2](vlm_analyzed_frames/matched_37.0s_a_reports_section_or_menu.jpg)

---

### Step 3: You see here, the income tax status

**Narration Time:** 45.0s  
**Visual Actually Appears:** 47.0s (+2.0s delay)  
**VLM Analysis:** Yes, the image shows an income tax status report or data. The webpage is from the Australian Taxation Office (ATO) and includes options to request reports such as "Income tax lodgment status" and "Out  
**Confidence:** 90%

![Step 3](vlm_analyzed_frames/matched_47.0s_income_tax_status_report_or_da.jpg)

---

### Step 4: we normally select all clients

**Narration Time:** 60.0s  
**Visual Actually Appears:** 60.0s (+0.0s delay)  
**VLM Analysis:** Yes, the image shows a filter with an "All Clients" option. The filter section is located below the "On demand reports" heading and includes checkboxes for different client categories such as "All cli  
**Confidence:** 90%

![Step 4](vlm_analyzed_frames/matched_60.0s_a_filter_or_dropdown_with_"All.jpg)

---

### Step 5: we can just download the files

**Narration Time:** 70.0s  
**Visual Actually Appears:** 70.0s (+0.0s delay)  
**VLM Analysis:** Yes, the image shows download buttons or options. Specifically, there are "Request" buttons next to various report descriptions, indicating that users can request these reports, which will then provid  
**Confidence:** 90%

![Step 5](vlm_analyzed_frames/matched_70.0s_download_buttons_or_options.jpg)

---


## Intelligence Summary

✅ **Real VLM Analysis**: Each frame was analyzed by Qwen2.5-VL-7B model  
✅ **Content Verification**: VLM confirmed frames actually show described content  
✅ **Temporal Alignment**: Found actual appearance times vs narration times  
✅ **No Shortcuts**: Using real 7B model with 15GB+ VRAM on GPU  

### Key Findings:

- Average visual delay: 2.8 seconds after narration
- VLM successfully identified 5 matching frames
- Frames now correctly show what's being described, not just temporal correlation
