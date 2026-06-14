# Pawchive-Favourites-Importer-from-kemono

Import your favourites from Kemono into Pawchive, using a Chrome debug port interface. This tool provides a clean Graphical User Interface (GUI) to automate the batch importing process effortlessly while keeping you updated with real-time logs.


<img width="782" height="652" alt="python_AAnVYECo9W" src="https://github.com/user-attachments/assets/8d4dea69-4a55-47c8-b1d6-95486a861e30" />


## Features

- **Batch Processing:** Paste multiple URLs at once (one per line) to import them in bulk.
- **Chrome Debug Integration:** Easily connect to your active Chrome session securely via the integrated debug port.
- **Real-Time Monitoring:** Live progress tracking showing total processed items, successfully favorited, skipped/already favorited, and error counts.
- **Execution Control:** Pause or halt operations instantly at any time using the **Stop** button, or refresh your logs with **Clear Output**.
- **Comprehensive Error Logging:** At the end of the execution, a detailed breakdown of failed URLs along with their specific failure reasons is provided for effortless troubleshooting.

---


## Installation

To run this script, you need to install the Playwright automation library.
Open your terminal or command prompt (**cmd**) and run the following combined command:

```bash
pip install playwright && playwright install
