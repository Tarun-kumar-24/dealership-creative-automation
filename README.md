Overview:- 

This project is an automated creative generation system built using Flask (Python), SQLite, and Pillow (PIL).

It generates Instagram-ready marketing creatives for multiple dealers under different accounts by dynamically combining:

Background images (user uploaded)
Dealer-specific templates
Dealer logos
Smart positioning logic

The system outputs creatives in multiple standard social media formats and packages them into a downloadable ZIP file.


Tech Stack:-

Backend: Flask (Python)
Database: SQLite3
Image Processing: Pillow (PIL)
Frontend: HTML + JavaScript
File Handling: OS, ZipFile


📂 Project Structure

Project/
│
├── app.py
├── database.db
├── uploads/
├── outputs/
│
├── static/
│   └── assets/
│       └── Dealership-panels/
│           ├── Tata-dealers/
│           ├── VW-dealers/
│
├── templates/
│   └── index.html
│
└── README.md




Core Features:- 

Multi-account dealer system
Dynamic asset loading per dealer
Smart logo selection (light/dark based on background brightness)
Template-based design system
Automated resizing for multiple output formats:
1080×1080 (Post)
1080×1350 (Portrait)
1080×1920 (Story)
ZIP export of all generated creatives
Saved dealer preferences (logo & template selection)



System Workflow:- 


User selects Account
Dealers are fetched from database
User uploads background image
System fetches dealer folder:
Logos
Templates
Selection logic runs:
Saved preferences OR auto-selection
Image processing pipeline executes:
Background resizing
Panel placement
Logo positioning
Final images generated in multiple sizes
All outputs compressed into ZIP file



Key Technical Logic:- 
1. Background Processing
Aspect ratio preserved using cover-style resizing
Ensures full-screen creative fit without distortion
2. Panel Placement
Panels are resized proportionally based on canvas width
Positioned at bottom of the image
Prevents overflow and maintains design consistency
3. Logo Intelligence System
Background brightness analysis using grayscale conversion
Auto-switch between:
logo-dark.png
logo-light.png
Smart placement in high-contrast corners


Challenges Faced & Solutions:- 

1. Image Cropping Issue (Background Distortion)

Problem:
Initial implementation cropped background images, leading to loss of important visual content.

Cause:
Use of crop() after resizing in cover method.

Solution:
Replaced logic with a controlled aspect-ratio resizing strategy ensuring full visual coverage without unwanted cropping in critical scenarios.


 2. Panel Overflow Outside Canvas

Problem:
Panels were extending beyond image boundaries in certain resolutions (especially 1080×1920).

Cause:
Only width scaling was applied without height constraint.

Solution:
Introduced height constraint logic:

Maximum panel height capped at 40% of canvas height
Dynamic scaling adjustment applied

3. Logo Not Rendering in Output

Problem:
In some cases logo was missing in final output images.

Cause:
Incorrect file path resolution and missing fallback validation.

Solution:

Added file existence checks (os.path.exists)
Implemented fallback logo selection system
Ensured correct dealer folder mapping


4. Dealer Folder Mismatch Issue

Problem:
Database dealer name did not match actual folder names.

Cause:
Inconsistent naming between DB and filesystem.

Solution:
Strict mapping enforced between:

dealerships.name
actual folder structure in assets directory


5. NoneType Crash in Image Pipeline

Problem:
Server crashed with:

AttributeError: 'NoneType' object has no attribute 'paste'

Cause:
Missing panel/logo file leading to invalid image object.

Solution:

Added pre-validation checks
Added logging for debugging missing assets
Safe fallback handling introduced



Key Learnings:-

File-based systems require strict naming consistency
PIL image pipeline must always include validation checks
Aspect ratio handling is critical in responsive creative systems
Debug logging is essential for production-level stability



Recommendations:-


1. AI-Based Layout Engine
Auto text positioning
Smart subject detection
Background-aware design balancing

2.  Cloud Storage Integration
Move assets to AWS S3 / Cloudinary
Remove dependency on local file system

3.  Queue System
Use Celery / Redis for bulk image generation
Prevent server blocking under heavy load

4.  Frontend Upgrade
React-based dashboard
Drag & drop creative editor
Live preview system

5.  Admin Panel
Upload templates/logos dynamically
Manage dealers and accounts from UI



Conclusion:-

This project successfully implements an end-to-end automated creative generation system that significantly reduces manual design effort in marketing workflows. Instead of relying on designers to manually create multiple variations of creatives for different dealers and platforms, the system automates the entire pipeline using structured data and image processing logic.

At its core, the system combines Flask for backend orchestration, SQLite for structured dealer and account management, and Pillow (PIL) for dynamic image composition. The workflow is designed to be fully data-driven, where each dealer is linked to a specific asset folder containing logos and templates, ensuring scalability across multiple brands and locations.

One of the key achievements of this system is the implementation of a smart image rendering engine. It handles background resizing while preserving aspect ratios, dynamically adjusts panel placement based on canvas dimensions, and intelligently selects and positions logos based on background brightness. This ensures that the final output is not only functional but also visually balanced and productionready.

During development, several real-world challenges were encountered, including:

inconsistent asset naming across folders
image cropping issues affecting visual quality
layout overflow on different Instagram formats
missing asset handling leading to runtime failures

Each of these issues was resolved through robust validation checks, improved resizing logic, and fallback mechanisms, making the system more stable and production-friendly.

Overall, this project demonstrates how automation can replace repetitive design tasks with intelligent systems, enabling faster content generation, consistency across branding, and reduced dependency on manual editing tools.

The system is designed in a way that it can be further scaled into a full-fledged creative automation platform, supporting cloud storage, AI-based layout optimization, and real-time design previews.