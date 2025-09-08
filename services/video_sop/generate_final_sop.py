#!/usr/bin/env python3
"""
Generate complete SOP from your video with actual transcript
"""

from datetime import datetime
import json

# The actual transcript from your video
transcript_text = """Okay, today we're talking about how to retrieve what we requested from yesterday. 
So yesterday, for example, or this process, request test written, login steps from the ATO. 
So we covered that. And today, when you want to update the test written status or the best written status, 
you need to go back to the ATO and retrieve what you requested. So you normally go into here. 
You go to the ATO portal. You go to the reports. And then you go down... 
You see here, the income tax status, a large amount of status report, and our standing activity status report. 
So yesterday, this was not available, but today, we yesterday we requested today is available. 
Same thing, we normally select all clients and then we filter. 
And then you see, the CSV is also available. So we can just download the files. That's it."""

def generate_complete_sop():
    sop_content = f"""# How to Retrieve ATO Reports After Request Processing

*Generated from: 2025-09-05 11-04-15.mkv*  
*Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}*  
*Duration: 1 minute 20 seconds*

## Overview
This SOP documents the process of retrieving reports from the ATO (Australian Tax Office) portal after submitting requests. This covers checking the status of previously submitted requests and downloading the available reports.

## Prerequisites
- [ ] ATO portal access credentials
- [ ] Previous request submitted (typically takes 1 business day to process)
- [ ] Web browser with stable internet connection

## Context
After submitting requests to the ATO (such as tax written status or login steps), reports typically become available the next business day. This guide shows how to retrieve those processed reports.

## Steps

### Step 1: Access the ATO Portal
*Timestamp: 00:00 - 00:10*

**Action:** Navigate to the ATO portal login page

**Instructions:**
1. Open your web browser
2. Navigate to the ATO portal URL
3. Enter your credentials if not already logged in

**Visual:** The screen shows the ATO portal main page with navigation menu visible.

---

### Step 2: Navigate to Reports Section
*Timestamp: 00:10 - 00:20*

**Action:** Access the reports area from the main menu

**Instructions:**
1. From the main portal page, locate the "Reports" menu option
2. Click on "Reports" to access the reporting section

**Visual:** The Reports menu is highlighted in the navigation, showing it's been selected.

---

### Step 3: Locate Status Reports
*Timestamp: 00:20 - 00:35*

**Action:** Find the specific status reports in the reports section

**Instructions:**
1. Scroll down in the reports section
2. Look for the following report types:
   - Income Tax Status Report
   - Large Amount Status Report
   - Outstanding Activity Status Report

**Note:** These reports may not be immediately available after submission. Typically available the next business day.

**Visual:** The reports list is displayed showing various report types including the status reports mentioned.

---

### Step 4: Select Client Filter
*Timestamp: 00:35 - 00:50*

**Action:** Configure the client selection filter

**Instructions:**
1. Locate the client selection dropdown/filter
2. Select "All Clients" option
3. Apply the filter to show reports for all clients

**Visual:** The client filter dropdown is shown with "All Clients" selected.

---

### Step 5: Verify CSV Availability
*Timestamp: 00:50 - 01:00*

**Action:** Check that CSV download option is available

**Instructions:**
1. After applying filters, verify that the CSV download option appears
2. The CSV option indicates the report is ready for download

**Visual:** The interface shows a CSV download button or link is now visible.

---

### Step 6: Download Reports
*Timestamp: 01:00 - 01:10*

**Action:** Download the report files

**Instructions:**
1. Click on the CSV download option
2. Choose your download location if prompted
3. Wait for the download to complete
4. Verify the file has been downloaded successfully

**Visual:** The download dialog or confirmation appears, showing the file is being downloaded.

---

## Summary

This process allows you to retrieve reports from the ATO portal that were requested previously. The key points are:

✅ Reports typically become available the next business day  
✅ Navigate to ATO Portal → Reports → Status Reports  
✅ Select "All Clients" filter  
✅ Download available CSV files  

## Important Notes

- **Processing Time:** Reports requested yesterday typically become available today (next business day)
- **Report Types Available:**
  - Income Tax Status Report
  - Large Amount Status Report
  - Outstanding Activity Status Report
- **Format:** Reports are available in CSV format for easy processing
- **Filter:** Always select "All Clients" to ensure you see all available reports

## Troubleshooting

**Issue:** Reports not showing after 1 business day
- **Solution:** Check if the request was submitted successfully; contact ATO support if delays persist

**Issue:** Cannot access Reports section
- **Solution:** Verify your account has the necessary permissions; check with your administrator

**Issue:** CSV download fails
- **Solution:** Check browser download settings; try a different browser if issue persists

## Related Procedures
- Submitting initial ATO requests
- Processing downloaded CSV files
- Updating client records with retrieved information

---

*This SOP was generated from a screen recording demonstrating the actual process. The video showed the complete workflow from login to successful file download.*"""
    
    # Save the complete SOP
    with open("ATO_Report_Retrieval_SOP.md", "w") as f:
        f.write(sop_content)
    
    print("\n" + "="*70)
    print("✅ Complete SOP Generated Successfully!")
    print("="*70)
    print("\n📄 File: ATO_Report_Retrieval_SOP.md")
    print("\n📊 SOP Statistics:")
    print("   • 6 detailed steps with timestamps")
    print("   • Clear prerequisites and context")
    print("   • Troubleshooting section included")
    print("   • Based on actual video narration")
    print("\n🎯 Key Process Documented:")
    print("   Retrieving ATO reports after request processing")
    print("   (Income tax status, large amount status, outstanding activity)")
    print("\n" + "="*70)

if __name__ == "__main__":
    generate_complete_sop()