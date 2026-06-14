# Pawchive-Favorites-Importer-from-kemono

Import your favourites from Kemono into Pawchive, using a Chrome debug port interface. This tool provides a clean Graphical User Interface (GUI) to automate the batch importing process effortlessly, with built-in support for extracting URLs directly from Kemono artists JSON exports.

<img width="822" height="852" alt="python_otAYYWdVuJ" src="https://github.com/user-attachments/assets/bd1dfd62-50fe-42a2-ac55-1fa9f12438d2" />


## Features

- **JSON Import Support:** Directly paste a Kemono artists export JSON structure or load a `.json` file to auto-generate target URLs.
- **Service Filtering:** Filter extracted JSON items via radio choices: select **Working only** (Patreon, Pixiv, Fanbox) or **All services**.
- **Flexible Manual Entry:** Skip the JSON workflow entirely if desired; you can still paste plain URLs directly into the URL field.
- **Chrome Debug Integration:** Securely connect to your active Chrome session using an integrated debug port.
- **Real-Time Monitoring:** Live tracking metrics showing total progress counters: successfully favorited, skipped/already favorited, and error counts.
- **Execution Controls:** Pause or halt active scripts with **Stop**, or refresh your console view using **Clear Output**.
- **Detailed Error Reporting:** Summarizes all failed URLs alongside their exact rejection causes at the end of execution.

---

## Installation

To run this script, you need to install the Playwright automation library.

Open your terminal or command prompt (**cmd**) and run the following combined command:

```bash
pip install playwright && playwright install
