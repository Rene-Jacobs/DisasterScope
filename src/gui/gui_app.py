# python -m src.gui.gui_app

# src/gui/gui_app.py
import os
import sys

# Add the parent directory to the path to fix the import issue
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
from typing import List, Optional
from dotenv import load_dotenv
import src.utils.search_api as search_api
import src.utils.article_analyzer as article_analyzer
import src.utils.report_generator as report_generator


# Define available sectors
PRIORITY_1_SECTORS = [
    "Chemical",
    "Commercial Facilities",
    "Communications",
    "Critical Manufacturing",
    "Dams",
    "Emergency Services",
    "Information Technology",
    "Nuclear",
    "Transportation",
    "Government Facilities",
]

PRIORITY_2_SECTORS = [
    "Energy",
    "Water",
    "Defense",
    "Financial",
    "Healthcare",
    "Food and Agriculture",
]

ALL_SECTORS = PRIORITY_1_SECTORS + PRIORITY_2_SECTORS

# Define disaster types
DISASTER_TYPES = [
    "Hurricane",
    "Earthquake",
    "Flood",
    "Fire",
    "Tornado",
    "Tsunami",
    "Drought",
    "Landslide",
    "Volcanic Eruption",
    "Winter Storm",
    "Heat Wave",
    "Other",
]


class RedirectText:
    """Class for redirecting stdout to a tkinter Text widget"""

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass


class DisasterAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Disaster Impact Analyzer")
        self.root.geometry("900x700")
        self.root.minsize(900, 700)

        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv("api_key", "")
        self.search_engine_id = os.getenv("search_engine_id", "")

        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create and place widgets
        self._create_widgets()

        # Status variables
        self.is_running = False

        # Selected sectors - start with no sectors selected
        self.selected_sectors = []

    def _create_widgets(self):
        # Create tabs
        self.tab_control = ttk.Notebook(self.main_frame)

        # Main tab (now will contain both disaster info and sectors)
        self.main_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.main_tab, text="Search & Sectors")

        # Settings tab
        self.settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab, text="Settings")

        self.tab_control.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Setup main tab
        self._setup_main_tab()

        # Setup settings tab
        self._setup_settings_tab()

    def _setup_main_tab(self):
        # Create a top frame to hold the two side-by-side sections
        top_frame = ttk.Frame(self.main_tab)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        # Disaster and Search info combined frame (left section)
        disaster_search_frame = ttk.LabelFrame(
            top_frame, text="Disaster & Search Settings", padding=10
        )
        disaster_search_frame.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5
        )

        # Disaster info subsection
        disaster_subframe = ttk.LabelFrame(
            disaster_search_frame, text="Disaster Information", padding=5
        )
        disaster_subframe.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(disaster_subframe, text="Disaster Type:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )

        self.disaster_type_var = tk.StringVar()
        self.disaster_type_combo = ttk.Combobox(
            disaster_subframe,
            textvariable=self.disaster_type_var,
            values=DISASTER_TYPES,
            width=20,
        )
        self.disaster_type_combo.set("-- Select Type --")
        self.disaster_type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.disaster_type_combo.bind(
            "<<ComboboxSelected>>", self.on_disaster_type_change
        )

        ttk.Label(disaster_subframe, text="Disaster Name:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.disaster_name_var = tk.StringVar()
        self.disaster_name_entry = ttk.Entry(
            disaster_subframe, textvariable=self.disaster_name_var, width=30
        )
        self.disaster_name_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Search options subsection
        options_subframe = ttk.LabelFrame(
            disaster_search_frame, text="Search Options", padding=5
        )
        options_subframe.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(options_subframe, text="Max Results:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.max_results_var = tk.IntVar(value=30)
        self.max_results_entry = ttk.Spinbox(
            options_subframe,
            from_=1,
            to=100,
            textvariable=self.max_results_var,
            width=5,
        )
        self.max_results_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(options_subframe, text="Output File:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.output_file_var = tk.StringVar(value="disaster_impact_report.xlsx")
        self.output_file_entry = ttk.Entry(
            options_subframe, textvariable=self.output_file_var, width=40
        )
        self.output_file_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        self.browse_btn = ttk.Button(
            options_subframe, text="Browse...", command=self.browse_output_file
        )
        self.browse_btn.grid(row=1, column=2, padx=5, pady=5)

        # Selected sectors preview
        ttk.Label(options_subframe, text="Selected Sectors:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.sectors_preview_var = tk.StringVar(value="No sectors selected")
        self.sectors_preview = ttk.Label(
            options_subframe, textvariable=self.sectors_preview_var, width=40
        )
        self.sectors_preview.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Sectors selection frame (right section)
        sectors_frame = ttk.LabelFrame(top_frame, text="Sector Selection", padding=10)
        sectors_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Priority 1 Sectors
        p1_frame = ttk.LabelFrame(sectors_frame, text="Priority 1 Sectors", padding=5)
        p1_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create checkboxes for Priority 1 Sectors
        self.p1_vars = {}
        for i, sector in enumerate(PRIORITY_1_SECTORS):
            var = tk.BooleanVar(value=False)  # All sectors start unchecked
            self.p1_vars[sector] = var
            cb = ttk.Checkbutton(
                p1_frame,
                text=sector,
                variable=var,
                command=self.update_selected_sectors,
            )
            cb.grid(row=i // 3, column=i % 3, sticky=tk.W, padx=10, pady=2)

        # Priority 2 Sectors
        p2_frame = ttk.LabelFrame(sectors_frame, text="Priority 2 Sectors", padding=5)
        p2_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create checkboxes for Priority 2 Sectors
        self.p2_vars = {}
        for i, sector in enumerate(PRIORITY_2_SECTORS):
            var = tk.BooleanVar(value=False)
            self.p2_vars[sector] = var
            cb = ttk.Checkbutton(
                p2_frame,
                text=sector,
                variable=var,
                command=self.update_selected_sectors,
            )
            cb.grid(row=i // 3, column=i % 3, sticky=tk.W, padx=10, pady=2)

        # Quick selection buttons
        sector_buttons_frame = ttk.Frame(sectors_frame)
        sector_buttons_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            sector_buttons_frame, text="Select All", command=self.select_all_sectors
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            sector_buttons_frame, text="Clear All", command=self.clear_all_sectors
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            sector_buttons_frame, text="Priority 1 Only", command=self.select_p1_sectors
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            sector_buttons_frame, text="Priority 2 Only", command=self.select_p2_sectors
        ).pack(side=tk.LEFT, padx=5)

        # Selected sectors count
        self.selected_count_var = tk.StringVar(value="Selected: 0 sectors")
        ttk.Label(
            sectors_frame, textvariable=self.selected_count_var, anchor=tk.E
        ).pack(fill=tk.X, padx=5, pady=5)

        # Bottom sections - below the top frame

        # Buttons frame
        buttons_frame = ttk.Frame(self.main_tab)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)

        self.search_btn = ttk.Button(
            buttons_frame, text="Start Analysis", command=self.start_analysis
        )
        self.search_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_btn = ttk.Button(
            buttons_frame, text="Stop", command=self.stop_analysis, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.open_results_btn = ttk.Button(
            buttons_frame, text="Open Results", command=self.open_results
        )
        self.open_results_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Create a Text widget for logging
        log_frame = ttk.LabelFrame(self.main_tab, text="Analysis Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, state=tk.DISABLED, height=15
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_tab, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.main_tab, textvariable=self.status_var, anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=5)

    def _setup_settings_tab(self):
        # API Settings frame
        api_frame = ttk.LabelFrame(
            self.settings_tab, text="Google API Settings", padding=10
        )
        api_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(api_frame, text="API Key:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.api_key_var = tk.StringVar(value=self.api_key)
        self.api_key_entry = ttk.Entry(
            api_frame, textvariable=self.api_key_var, width=50, show="*"
        )
        self.api_key_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(api_frame, text="Search Engine ID:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.search_engine_id_var = tk.StringVar(value=self.search_engine_id)
        self.search_engine_id_entry = ttk.Entry(
            api_frame, textvariable=self.search_engine_id_var, width=50
        )
        self.search_engine_id_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Save settings button
        self.save_settings_btn = ttk.Button(
            api_frame, text="Save Settings", command=self.save_settings
        )
        self.save_settings_btn.grid(row=2, column=1, sticky=tk.E, padx=5, pady=5)

        # Help text
        help_frame = ttk.LabelFrame(self.settings_tab, text="Help", padding=10)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        help_text = (
            "This application searches for articles about a natural disaster's impact on critical infrastructure sectors."
            "\n\nTo use this application:"
            "\n1. Select a disaster type (Hurricane, Earthquake, etc.)"
            "\n2. Enter the disaster name (e.g., 'Katrina', 'Camp Fire')"
            "\n3. Select the sectors you want to analyze"
            "\n4. Set the maximum number of search results"
            "\n5. Choose where to save the Excel report"
            "\n6. Click 'Start Analysis' to begin"
            "\n\nYou must provide Google API credentials in the Settings tab."
            "\nThese can be obtained from the Google Cloud Console."
        )

        help_text_widget = scrolledtext.ScrolledText(help_frame, wrap=tk.WORD)
        help_text_widget.insert(tk.INSERT, help_text)
        help_text_widget.configure(state="disabled")
        help_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def on_disaster_type_change(self, event=None):
        # Handle disaster type change if needed
        pass

    def select_all_sectors(self):
        """Select all sectors"""
        for var in list(self.p1_vars.values()) + list(self.p2_vars.values()):
            var.set(True)
        self.update_selected_sectors()

    def clear_all_sectors(self):
        """Clear all sector selections"""
        for var in list(self.p1_vars.values()) + list(self.p2_vars.values()):
            var.set(False)
        self.update_selected_sectors()

    def select_p1_sectors(self):
        """Select only Priority 1 sectors"""
        for var in self.p1_vars.values():
            var.set(True)
        for var in self.p2_vars.values():
            var.set(False)
        self.update_selected_sectors()

    def select_p2_sectors(self):
        """Select only Priority 2 sectors"""
        for var in self.p1_vars.values():
            var.set(False)
        for var in self.p2_vars.values():
            var.set(True)
        self.update_selected_sectors()

    def update_selected_sectors(self):
        """Update the selected sectors list based on checkboxes"""
        self.selected_sectors = []

        # Add selected Priority 1 sectors
        for sector, var in self.p1_vars.items():
            if var.get():
                self.selected_sectors.append(sector)

        # Add selected Priority 2 sectors
        for sector, var in self.p2_vars.items():
            if var.get():
                self.selected_sectors.append(sector)

        # Update the sectors preview and count
        if self.selected_sectors:
            self.sectors_preview_var.set(
                ", ".join(self.selected_sectors)
                if len(self.selected_sectors) <= 3
                else f"{len(self.selected_sectors)} sectors selected"
            )
        else:
            self.sectors_preview_var.set("No sectors selected")

        self.selected_count_var.set(
            f"Selected: {len(self.selected_sectors)} sector{'s' if len(self.selected_sectors) > 1 else ''}"
        )

    def browse_output_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=self.output_file_var.get(),
        )
        if filename:
            self.output_file_var.set(filename)

    def save_settings(self):
        # Save API key and Search Engine ID to .env file
        api_key = self.api_key_var.get().strip()
        search_engine_id = self.search_engine_id_var.get().strip()

        if not api_key or not search_engine_id:
            messagebox.showerror("Error", "API Key and Search Engine ID are required")
            return

        try:
            with open(".env", "w") as f:
                f.write(f"api_key={api_key}\n")
                f.write(f"search_engine_id={search_engine_id}\n")

            # Update current session variables
            self.api_key = api_key
            self.search_engine_id = search_engine_id

            messagebox.showinfo("Success", "Settings saved successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def start_analysis(self):
        # Validate input
        disaster_type = self.disaster_type_var.get().strip()
        disaster_name = self.disaster_name_var.get().strip()

        if not disaster_type or disaster_type == "-- Select Type --":
            messagebox.showerror("Error", "Please select a disaster type")
            return

        if not disaster_name:
            messagebox.showerror("Error", "Please enter a disaster name")
            return

        if not self.api_key or not self.search_engine_id:
            messagebox.showerror(
                "Error",
                "API Key and Search Engine ID are required. Please check Settings.",
            )
            return

        if not self.selected_sectors:
            messagebox.showerror(
                "Error", "Please select at least one sector to analyze"
            )
            return

        # Disable UI elements during processing
        self.search_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.is_running = True

        # Redirect stdout to our log widget
        self.old_stdout = sys.stdout
        sys.stdout = RedirectText(self.log_text)

        # Clear log
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

        # Reset progress
        self.progress_var.set(0)
        self.status_var.set("Analyzing...")

        # Start analysis in a separate thread
        self.analysis_thread = threading.Thread(
            target=self.run_analysis,
            args=(
                disaster_type,
                disaster_name,
                self.selected_sectors,
                self.max_results_var.get(),
                self.output_file_var.get(),
            ),
        )
        self.analysis_thread.daemon = True
        self.analysis_thread.start()

        # Start a timer to check the thread status
        self.root.after(100, self.check_thread)

    def run_analysis(
        self, disaster_type, disaster_name, sectors, max_results, output_file
    ):
        try:
            # Set up asyncio event loop for this thread
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # If there's no event loop in the current thread, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Update status
            self.update_status("Constructing search query...")

            # Construct the query
            query = (
                f"{disaster_name} {disaster_type.lower()} effects on US infrastructure"
            )

            # Search for articles
            self.update_status(
                f"Searching for articles related to sectors: {', '.join(sectors)}..."
            )
            results = search_api.search_articles(
                query,
                self.api_key,
                self.search_engine_id,
                sectors,
                max_results,
                disaster_type,
            )

            if not results:
                self.update_status("No relevant articles found.")
                return

            self.update_status(
                f"Found {len(results)} relevant articles. Processing in parallel..."
            )

            # Extract article URLs and filter out None values - THIS IS THE FIX
            article_urls = []
            for result in results:
                url = result.get("link")
                if url and isinstance(url, str):  # Only add valid URL strings
                    article_urls.append(url)

            if not article_urls:
                self.update_status("No valid article URLs found.")
                return

            # Process articles in parallel
            self.update_status(
                f"Analyzing {len(article_urls)} articles concurrently..."
            )
            self.root.after(
                0, lambda: self.progress_var.set(10)
            )  # Update progress to 10%

            # Use the parallel processing function from article_analyzer
            analysis_results = article_analyzer.analyze_articles(
                article_urls, disaster_type
            )

            # Create a dictionary for quick lookup of analysis results by URL
            analysis_dict = {}
            for i, res in enumerate(analysis_results):
                url = res.get("url")
                if url:
                    analysis_dict[url] = res

                    # Update progress in batches to avoid UI lag
                    if i % 5 == 0 or i == len(analysis_results) - 1:
                        progress = 10 + (i / len(analysis_results)) * 70  # 10% to 80%
                        self.root.after(0, lambda p=progress: self.progress_var.set(p))

            self.update_status(
                f"Analysis complete, processing {len(analysis_dict)} results..."
            )
            self.root.after(0, lambda: self.progress_var.set(80))  # Update to 80%

            # Merge search results with analysis results
            articles = []
            for result in results:
                link = result.get("link")
                if link and link in analysis_dict:
                    analysis = analysis_dict[link]

                    # Get publication date from analysis result
                    result["publication_date"] = analysis.get(
                        "publication_info", {}
                    ).get("date", "")
                    result["disaster_type"] = disaster_type

                    # Get impact details
                    impact_info = analysis.get("impact_info", {})
                    impact_details = impact_info.get("raw_content", "")

                    # If we couldn't extract impact details, use the snippet as a fallback
                    if not impact_details:
                        print(
                            f"  - No specific impact details found, using snippet as fallback"
                        )
                        impact_details = result.get("snippet", "")

                    result["impact_details"] = impact_details
                    articles.append(result)

            # Generate Excel output report
            self.update_status("Generating Excel report...")
            self.root.after(0, lambda: self.progress_var.set(90))  # Update to 90%

            report_generator.generate_excel_report(articles, output_file)

            self.update_status(
                f"Analysis complete. Excel report saved to: {output_file}"
            )
            self.root.after(0, lambda: self.progress_var.set(100))  # Update to 100%

        except Exception as e:
            self.update_status(f"Error during analysis: {str(e)}")
            print(f"ERROR: {str(e)}")
            import traceback

            print(traceback.format_exc())

    def update_status(self, message):
        print(message)
        self.root.after(0, lambda msg=message: self.status_var.set(msg))

    def check_thread(self):
        if self.analysis_thread.is_alive() and self.is_running:
            # Thread still running, check again after a delay
            self.root.after(100, self.check_thread)
        else:
            # Thread completed or stopped, restore UI
            sys.stdout = self.old_stdout
            self.search_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.DISABLED)
            self.is_running = False

    def stop_analysis(self):
        if self.is_running:
            self.is_running = False
            self.update_status("Stopping analysis...")

    def open_results(self):
        output_file = self.output_file_var.get()
        if os.path.exists(output_file):
            try:
                # Use the default application to open the Excel file
                if sys.platform == "win32":
                    os.startfile(output_file)
                elif sys.platform == "darwin":  # macOS
                    import subprocess

                    subprocess.call(["open", output_file])
                else:  # Linux
                    import subprocess

                    subprocess.call(["xdg-open", output_file])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
        else:
            messagebox.showerror("Error", f"File not found: {output_file}")


if __name__ == "__main__":

    root = tk.Tk()
    app = DisasterAnalyzerApp(root)
    root.mainloop()
    # To run the GUI, execute: python -m src.gui.gui_app
