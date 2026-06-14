import os
import json
import time
import threading
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ─── Constants ──────────────────────────────────────────────────────────────
DEBUG_PORT   = 9222
PROFILE_DIR  = os.path.join(os.path.expanduser("~"), "ChromePawchiveProfile")
LOGIN_URL    = "https://pawchive.st/account/login"
BASE_URL     = "https://pawchive.st"

# Services that are currently working for the favoriting automation
WORKING_SERVICES = {"patreon", "pixiv", "fanbox"}

# ─── HARDCODED LOGIN — edit these ──────────────────────────────────────────
HARD_USERNAME = "your_username_here"
HARD_PASSWORD = "your_password_here"
# ────────────────────────────────────────────────────────────────────────────


class FavoriterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pawchive Favoriter")
        self.root.geometry("820x820")
        self.root.configure(bg="#1e1e2e")

        self.stop_flag = False
        self.thread = None

        # Counters
        self.total = 0
        self.done = 0
        self.fav_count = 0
        self.skip_count = 0
        self.error_count = 0

        self._build_ui()

    # ── UI BUILD ────────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = {"padx": 6, "pady": 4}

        BG = "#1e1e2e"
        FG = "#cdd6f4"
        ENTRY = "#313244"
        ACCENT = "#7c6af7"

        self.root.configure(bg=BG)

        style_label = dict(bg=BG, fg=FG, font=("Segoe UI", 10))

        style_entry = dict(
            bg=ENTRY,
            fg=FG,
            insertbackground=FG,
            relief="flat",
            font=("Consolas", 10)
        )

        style_btn = dict(
            bg=ACCENT,
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=5,
            cursor="hand2"
        )

        # Login row (username + password on same line)
        login_frame = tk.Frame(self.root, bg=BG)
        login_frame.pack(fill="x", **pad)

        tk.Label(login_frame, text="Username:", **style_label).pack(side="left")
        self.username_entry = tk.Entry(login_frame, width=20, **style_entry)
        self.username_entry.insert(0, HARD_USERNAME)
        self.username_entry.pack(side="left", padx=(4, 12))

        tk.Label(login_frame, text="Password:", **style_label).pack(side="left")
        self.password_entry = tk.Entry(login_frame, width=20, **style_entry)  # not masked, per request
        self.password_entry.insert(0, HARD_PASSWORD)
        self.password_entry.pack(side="left", padx=(4, 0))

        # ── JSON area (top) ─────────────────────────────────────────────
        json_header = tk.Frame(self.root, bg=BG)
        json_header.pack(fill="x", padx=6, pady=(4, 0))
        tk.Label(json_header, text="JSON (paste artists export):", **style_label).pack(side="left")

        self.load_json_btn = tk.Button(
            json_header, text="📂  Load JSON File",
            command=self._load_json_file, **style_btn)
        self.load_json_btn.pack(side="right")

        self.json_text = scrolledtext.ScrolledText(
            self.root, height=6, wrap="none",
            bg=ENTRY, fg=FG, insertbackground=FG,
            relief="flat", font=("Consolas", 10)
        )
        self.json_text.pack(fill="x", padx=6, pady=(2, 4))

        # Filter radio + extract button row
        filter_frame = tk.Frame(self.root, bg=BG)
        filter_frame.pack(fill="x", padx=6, pady=(0, 6))

        tk.Label(filter_frame, text="Services to extract:", **style_label).pack(side="left")

        self.service_filter = tk.StringVar(value="working")

        radio_style = dict(
            bg=BG, fg=FG, selectcolor=ENTRY,
            activebackground=BG, activeforeground=FG,
            font=("Segoe UI", 10)
        )

        tk.Radiobutton(
            filter_frame, text="Working only (Patreon, Pixiv, Fanbox)",
            variable=self.service_filter, value="working", **radio_style
        ).pack(side="left", padx=(8, 4))

        tk.Radiobutton(
            filter_frame, text="All services",
            variable=self.service_filter, value="all", **radio_style
        ).pack(side="left", padx=(4, 12))

        self.extract_btn = tk.Button(
            filter_frame, text="⬇  Extract URLs from JSON",
            command=self._extract_urls_from_json, **style_btn)
        self.extract_btn.pack(side="right")

        # ── URL area (middle) ───────────────────────────────────────────
        tk.Label(self.root, text="URLs (one per line):", **style_label).pack(anchor="w", padx=6)
        self.url_text = scrolledtext.ScrolledText(
            self.root, height=8, wrap="none",
            bg=ENTRY, fg=FG, insertbackground=FG,
            relief="flat", font=("Consolas", 10)
        )
        self.url_text.pack(fill="x", padx=6, pady=(0, 6))

        # Buttons row (in line)
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(fill="x", padx=6, pady=4)

        style_chrome = dict(**style_btn)
        style_chrome["bg"] = "#e08000"
        self.chrome_btn = tk.Button(
            btn_frame, text="🌐  Open Chrome",
            command=self._launch_chrome, **style_chrome)
        self.chrome_btn.pack(side="left", padx=(0, 8))

        self.start_btn = tk.Button(
            btn_frame, text="▶  Start",
            command=self._start_automation, **style_btn)
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = tk.Button(
            btn_frame, text="■  Stop",
            command=self._stop_automation, state="disabled", **style_btn)
        self.stop_btn.pack(side="left", padx=(0, 8))

        self.clear_btn = tk.Button(
            btn_frame, text="🧹  Clear Output",
            command=self._clear_output, **style_btn)
        self.clear_btn.pack(side="left", padx=(0, 8))

        # Status counter
        self.status_label = tk.Label(self.root, text=self._status_text(), anchor="w", **style_label)
        self.status_label.pack(fill="x", padx=6, pady=(0, 4))

        # ── Output area (bottom) ────────────────────────────────────────
        tk.Label(self.root, text="Output:", **style_label).pack(anchor="w", padx=6)
        self.output_box = scrolledtext.ScrolledText(
            self.root, wrap="word", state="normal",
            bg=ENTRY, fg=FG, insertbackground=FG,
            relief="flat", font=("Consolas", 10)
        )
        self.output_box.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self._build_context_menu()

    def _build_context_menu(self):
        self.context_menu = tk.Menu(
            self.output_box, tearoff=0,
            bg="#313244", fg="#cdd6f4",
            activebackground="#7c6af7", activeforeground="white"
        )
        self.context_menu.add_command(label="Copy", command=self._copy_selection)
        self.context_menu.add_command(label="Select All", command=self._select_all)
        self.output_box.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _copy_selection(self):
        try:
            selected = self.output_box.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
        except tk.TclError:
            pass

    def _select_all(self):
        self.output_box.tag_add("sel", "1.0", "end")

    def _status_text(self):
        return (f"Progress: {self.done}/{self.total}  |  "
                f"Favorited: {self.fav_count}  |  "
                f"Already favorited: {self.skip_count}  |  "
                f"Errors: {self.error_count}")

    def _update_status(self):
        self.status_label.config(text=self._status_text())

    def _clear_output(self):
        self.output_box.delete("1.0", "end")

    # ── JSON HANDLING ──────────────────────────────────────────────────────
    def _load_json_file(self):
        path = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.json_text.delete("1.0", "end")
            self.json_text.insert("1.0", content)
            self.log(f"✔ Loaded JSON file: {path}")
        except Exception as e:
            self.log(f"❌ Error reading JSON file: {e}")

    def _extract_urls_from_json(self):
        raw = self.json_text.get("1.0", "end").strip()
        if not raw:
            messagebox.showwarning("No JSON", "Paste or load a JSON export first.")
            return

        try:
            data = json.loads(raw)
        except Exception as e:
            messagebox.showerror("Invalid JSON", f"Could not parse JSON: {e}")
            return

        artists = data.get("artists", []) if isinstance(data, dict) else data
        if not isinstance(artists, list):
            messagebox.showerror("Invalid JSON", "Expected an 'artists' list in the JSON.")
            return

        only_working = self.service_filter.get() == "working"

        urls = []
        skipped = 0
        for artist in artists:
            try:
                service = (artist.get("service") or "").strip().lower()
                artist_id = artist.get("id")
                if not service or artist_id is None:
                    skipped += 1
                    continue
                if only_working and service not in WORKING_SERVICES:
                    skipped += 1
                    continue
                urls.append(f"{BASE_URL}/{service}/user/{artist_id}")
            except Exception:
                skipped += 1

        if not urls:
            messagebox.showwarning("No URLs", "No matching URLs could be extracted from the JSON.")
            return

        self.url_text.delete("1.0", "end")
        self.url_text.insert("1.0", "\n".join(urls))

        mode_text = "working services only" if only_working else "all services"
        self.log(f"✔ Extracted {len(urls)} URL(s) ({mode_text}). Skipped {skipped}.")

    # ── LOG ─────────────────────────────────────────────────────────────────
    def log(self, msg):
        def append():
            self.output_box.insert("end", msg + "\n")
            self.output_box.see("end")
        self.root.after(0, append)

    # ── CHROME LAUNCH ──────────────────────────────────────────────────────
    def _launch_chrome(self):
        threading.Thread(target=self._launch_chrome_thread, daemon=True).start()

    def _launch_chrome_thread(self):
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            self.log("❌ Chrome not found. Check the installation path.")
            return
        try:
            subprocess.Popen([
                chrome_path,
                f"--remote-debugging-port={DEBUG_PORT}",
                f"--user-data-dir={PROFILE_DIR}",
                "--no-first-run",
                "--no-default-browser-check",
            ])
            self.log(f"✔ Starting Chrome with --remote-debugging-port={DEBUG_PORT}…")
            import urllib.request
            for attempt in range(20):
                time.sleep(1)
                try:
                    urllib.request.urlopen(
                        f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=2
                    )
                    self.log("✔ Chrome ready!")
                    return
                except Exception:
                    self.log(f"   Waiting for Chrome… ({attempt + 1}/20)")
            self.log("⚠ Chrome took too long. Try starting the automation anyway.")
        except Exception as e:
            self.log(f"❌ Error launching Chrome: {e}")

    # ── AUTOMATION CONTROL ────────────────────────────────────────────────
    def _start_automation(self):
        urls_raw = self.url_text.get("1.0", "end").strip()
        if not urls_raw:
            messagebox.showwarning("No URLs", "Paste at least one URL in the URL box.")
            return

        urls = [line.strip() for line in urls_raw.splitlines() if line.strip()]
        if not urls:
            messagebox.showwarning("No URLs", "No valid URL found.")
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        self.total = len(urls)
        self.done = 0
        self.fav_count = 0
        self.skip_count = 0
        self.error_count = 0
        self._update_status()

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.stop_flag = False

        self.thread = threading.Thread(
            target=self._run_automation, args=(urls, username, password), daemon=True
        )
        self.thread.start()

    def _stop_automation(self):
        self.stop_flag = True
        self.log("⏹ Stopping… (will finish after the current link)")

    def _on_finish(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    # ── PLAYWRIGHT AUTOMATION ─────────────────────────────────────────────
    def _is_logged_in(self, page):
        """Checks whether the session is already authenticated."""
        try:
            page.goto("https://pawchive.st/artists?logged_in=yes&role=consumer",
                      wait_until="domcontentloaded", timeout=30000)
            if self._is_login_page(page):
                return False
            return True
        except Exception:
            return False

    def _do_login(self, page, username, password):
        """Performs login on the login page. Returns True if logged in (already or after submitting)."""
        try:
            if self._is_logged_in(page):
                self.log("✔ Session already logged in.")
                return True

            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("#login_form", timeout=15000)
            page.fill("#old-username", username)
            page.fill("#old-password", password)
            page.click("#login_form button[type='submit']")
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            self.log("✔ Login submitted.")
            return True
        except PWTimeout:
            self.log("❌ Error: timeout during login (form not found).")
            return False
        except Exception as e:
            self.log(f"❌ Error during login: {e}")
            return False

    def _is_login_page(self, page):
        try:
            return page.locator("#login_form").count() > 0
        except Exception:
            return False

    def _favorite_url(self, page, url, username, password, errors):
        """
        Navigates to url and clicks favorite if not already favorited.
        Returns one of: "favorited", "already", "error"
        Handles session-expiry by re-logging in and retrying once.
        """
        for attempt in range(2):  # original attempt + 1 retry after re-login
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Session expired -> redirected to login page
                if self._is_login_page(page):
                    if attempt == 0:
                        self.log("⚠ Session expired. Trying to log in again…")
                        if self._do_login(page, username, password):
                            continue  # retry navigation to the same url
                        else:
                            errors.append(f"{url} -> failed to re-authenticate")
                            return "error"
                    else:
                        errors.append(f"{url} -> still on login page after re-authentication")
                        return "error"

                # Wait for the header/favourite button to appear
                try:
                    page.wait_for_selector(".user-header .user-header__favourite", timeout=15000)
                except PWTimeout:
                    errors.append(f"{url} -> favorite button not found (timeout)")
                    return "error"

                fav_btn = page.locator(".user-header .user-header__favourite").first
                classes = fav_btn.get_attribute("class") or ""

                if "user-header__favourite--unfav" in classes:
                    self.log(f"⏭ Already favorited: {url}")
                    return "already"

                fav_btn.click()

                # Wait for class to update to the unfav state
                try:
                    page.wait_for_selector(
                        ".user-header .user-header__favourite.user-header__favourite--unfav",
                        timeout=10000,
                    )
                    self.log(f"★ Favorited: {url}")
                    return "favorited"
                except PWTimeout:
                    errors.append(f"{url} -> click sent but state did not update (timeout)")
                    return "error"

            except PWTimeout:
                if attempt == 0:
                    self.log(f"⚠ Timeout loading {url}. Checking session…")
                    if self._is_login_page(page) or True:
                        # try re-login then retry once
                        if self._do_login(page, username, password):
                            continue
                errors.append(f"{url} -> timeout loading the page")
                return "error"
            except Exception as e:
                errors.append(f"{url} -> unexpected error: {e}")
                return "error"

        errors.append(f"{url} -> failed after re-authentication attempts")
        return "error"

    def _run_automation(self, urls, username, password):
        errors = []
        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
                except Exception as e:
                    self.log(f"❌ Error connecting to Chrome (port {DEBUG_PORT}): {e}")
                    self.log("   Make sure you clicked 'Open Chrome' first.")
                    self._finish_with_errors(errors)
                    return

                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = context.pages[0] if context.pages else context.new_page()

                # Initial login
                self.log("🔐 Logging in…")
                if not self._do_login(page, username, password):
                    self.log("❌ Initial login failed. Aborting.")
                    self._finish_with_errors(errors)
                    return

                self.log("✔ Ready. Starting to process links…")

                for url in urls:
                    if self.stop_flag:
                        self.log("⏹ Automation stopped by user.")
                        break

                    result = self._favorite_url(page, url, username, password, errors)

                    if result == "favorited":
                        self.fav_count += 1
                    elif result == "already":
                        self.skip_count += 1
                    elif result == "error":
                        self.error_count += 1

                    self.done += 1
                    self.root.after(0, self._update_status)

                self.log("✔ Processing complete.")
        except Exception as e:
            self.log(f"❌ Fatal error: {e}")
        finally:
            self._finish_with_errors(errors)

    def _finish_with_errors(self, errors):
        if errors:
            self.log("\n──── ERRORS ────")
            for err in errors:
                self.log(f"❌ {err}")
        self.root.after(0, self._on_finish)


if __name__ == "__main__":
    root = tk.Tk()
    app = FavoriterGUI(root)
    root.mainloop()
