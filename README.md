# Calyx: Remote Wound Intelligence

## Headline
**The clinical middleman turning wound photos into life-saving data.**

## Inspiration
30% of chronic wounds lead to hospital readmission because warning signs are invisible at home. We built **Calyx** to serve as the critical _middleman_ between patients and medical teams, replacing passive "photo galleries" with a quantitative reasoning engine.

## What it does
Calyx uses **Computer Vision** to act as a "digital ruler," measuring wound area and tissue health from a smartphone. It cross-references these scans with a _clinical knowledge graph_ to alert doctors if a patient's **biomarkers**—like high blood sugar—are stalling their recovery.

## How we built it
The platform is powered by a **Python** backend using:
* **The Eyes:** OpenCV and _K-Means_ for tissue segmentation.
* **The Brain:** _NetworkX_ to map clinical comorbidities.
* **The Interface:** A **Streamlit** frontend featuring a patient webcam portal and a doctor dashboard with **Plotly** healing charts.

## Challenges we ran into
* **Calibration:** Achieving accuracy across different cameras was difficult. We used a _calibration coin_ as a real-world reference to calculate precise area in cm2.
* **Logic Mapping:** Translating medical literature into a **Directed Graph** required complex weighting to ensure _BFS traversal_ prioritized life-critical risks.

## Accomplishments that we're proud of
* **Computer Vision Precision:** Using **OpenCV** to turn raw pixels into quantitative data like "granulation is up 8%."
* **System Reasoning:** Building a tool that "knows" a wound is failing because of _underlying pathology_, not just appearance.

## What we learned
* **Knowledge Graphs:** We learned exactly how **Knowledge Graphs** work by using **NetworkX** to map out complex relationships and navigating them with _BFS traversal_ logic.
* **K-Means Clustering:** We learned how **K-Means Clustering** works by using it to segment images into distinct color zones to quantify different tissue types automatically.

## What's next for ChroniScan
* **Real-Time Processing:** We want to implement **Live Webcam Capture** for real-time image processing instead of simple file uploads to provide instant feedback on calibration and quality.
* **3D Analysis:** Moving beyond static images into **video-based 3D wound depth analysis** for more accurate volume tracking.
