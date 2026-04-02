#!/usr/bin/env python3
"""PS3 CFW to OFW Game and App Converter - GUI"""

import os
import sys
import subprocess
import threading
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

VERSION = "0.5"

TITLE_ID_MAP = {
    "BLJS": "NPJB", "BLJM": "NPJB", "BCJS": "NPJA",
    "BLUS": "NPUB", "BCUS": "NPUA",
    "BLES": "NPEB", "BCES": "NPEA",
    "BLAS": "NPHB", "BCAS": "NPHA",
    "BLKS": "NPKB", "BCKS": "NPKA",
}

SKIP_OPTIONS = {
    0: ("Convert All Files", []),
    1: ("Skip SDAT", [".sdat"]),
    2: ("Skip SDAT/EDAT", [".sdat", ".edat"]),
    3: ("Skip SDAT/EDAT/SPRX", [".sdat", ".edat", ".sprx"]),
    4: ("Skip SDAT/EDAT/SPRX/SELF", [".sdat", ".edat", ".sprx", ".self"]),
}


class PS3ConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"PS3 CFW to OFW Converter v{VERSION}")
        self.geometry("820x700")
        self.minsize(750, 600)
        self.configure(bg="#1e1e2e")

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.bin_path = self._find_bin_path()
        self.ps3_game_dir = tk.StringVar()
        self.game_title = tk.StringVar(value="--")
        self.disc_title_id = tk.StringVar(value="--")
        self.game_version = tk.StringVar(value="--")
        self.app_version = tk.StringVar(value="--")
        self.converted_id = tk.StringVar()
        self.custom_id = tk.StringVar()
        self.update_status = tk.StringVar(value="Not checked")
        self.update_url = ""
        self.update_available = False
        self.skip_var = tk.IntVar(value=1)
        self.download_update = tk.BooleanVar(value=True)
        self.converting = False

        self._build_ui()
        self._auto_detect_ps3_game()

    def _find_bin_path(self):
        for p in [os.path.join(self.script_dir, "bin"),
                  os.path.join(self.script_dir, "tool")]:
            if os.path.isfile(os.path.join(p, "make_npdata.exe")):
                return p
        return os.path.join(self.script_dir, "bin")

    def _tool(self, name):
        return os.path.join(self.bin_path, name)

    # ── UI construction ──────────────────────────────────────────

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#89b4fa"
        entry_bg = "#313244"
        btn_bg = "#45475a"
        green = "#a6e3a1"
        red = "#f38ba8"
        yellow = "#f9e2af"

        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=bg, foreground=accent, font=("Segoe UI", 11, "bold"))
        style.configure("Title.TLabel", background=bg, foreground=accent, font=("Segoe UI", 14, "bold"))
        style.configure("Green.TLabel", background=bg, foreground=green)
        style.configure("Red.TLabel", background=bg, foreground=red)
        style.configure("Yellow.TLabel", background=bg, foreground=yellow)
        style.configure("TButton", background=btn_bg, foreground=fg, font=("Segoe UI", 10), padding=6)
        style.map("TButton", background=[("active", accent)])
        style.configure("Accent.TButton", background=accent, foreground="#1e1e2e", font=("Segoe UI", 10, "bold"), padding=8)
        style.map("Accent.TButton", background=[("active", "#74c7ec")])
        style.configure("TRadiobutton", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.map("TRadiobutton", background=[("active", bg)])
        style.configure("TCheckbutton", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", bg)])
        style.configure("TLabelframe", background=bg, foreground=accent)
        style.configure("TLabelframe.Label", background=bg, foreground=accent, font=("Segoe UI", 10, "bold"))

        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="PS3 CFW to OFW Game Converter", style="Title.TLabel").pack(anchor="w")

        # ── Directory selection ──
        dir_frame = ttk.LabelFrame(main, text="PS3_GAME Directory", padding=8)
        dir_frame.pack(fill="x", pady=(8, 4))
        row = ttk.Frame(dir_frame)
        row.pack(fill="x")
        entry = tk.Entry(row, textvariable=self.ps3_game_dir, bg=entry_bg, fg=fg,
                         insertbackground=fg, font=("Consolas", 10), relief="flat")
        entry.pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Button(row, text="Browse...", command=self._browse_dir).pack(side="right", padx=(6, 0))
        ttk.Button(row, text="Detect Game", command=self._detect_game).pack(side="right", padx=(6, 0))

        # ── Game info ──
        info_frame = ttk.LabelFrame(main, text="Detected Game Info", padding=8)
        info_frame.pack(fill="x", pady=4)
        grid = ttk.Frame(info_frame)
        grid.pack(fill="x")
        for i, (label, var) in enumerate([
            ("Title:", self.game_title),
            ("Disc Title ID:", self.disc_title_id),
            ("Version:", self.game_version),
            ("App Version:", self.app_version),
        ]):
            ttk.Label(grid, text=label, style="Header.TLabel").grid(row=i, column=0, sticky="w", padx=(0, 8))
            ttk.Label(grid, textvariable=var).grid(row=i, column=1, sticky="w")

        # ── Conversion settings ──
        conv_frame = ttk.LabelFrame(main, text="Conversion Settings", padding=8)
        conv_frame.pack(fill="x", pady=4)

        id_row = ttk.Frame(conv_frame)
        id_row.pack(fill="x", pady=2)
        ttk.Label(id_row, text="Output Game ID:").pack(side="left")
        id_entry = tk.Entry(id_row, textvariable=self.custom_id, width=14, bg=entry_bg, fg=fg,
                            insertbackground=fg, font=("Consolas", 10), relief="flat")
        id_entry.pack(side="left", padx=8, ipady=3)
        ttk.Label(id_row, text="(leave blank for auto:").pack(side="left")
        ttk.Label(id_row, textvariable=self.converted_id, style="Green.TLabel").pack(side="left")
        ttk.Label(id_row, text=")").pack(side="left")

        ttk.Label(conv_frame, text="Title ID Mapping Reference:", style="Header.TLabel").pack(anchor="w", pady=(6, 2))
        mapping_text = (
            "BLJS/BLJM -> NPJB  |  BCJS -> NPJA  |  BLUS -> NPUB  |  BCUS -> NPUA\n"
            "BLES -> NPEB  |  BCES -> NPEA  |  BLAS -> NPHB  |  BCAS -> NPHA\n"
            "BLKS -> NPKB  |  BCKS -> NPKA"
        )
        tk.Label(conv_frame, text=mapping_text, bg="#1e1e2e", fg="#a6adc8",
                 font=("Consolas", 9), justify="left").pack(anchor="w")

        # ── Update ──
        upd_frame = ttk.LabelFrame(main, text="Game Update", padding=8)
        upd_frame.pack(fill="x", pady=4)
        upd_row = ttk.Frame(upd_frame)
        upd_row.pack(fill="x")
        ttk.Label(upd_row, text="Status:").pack(side="left")
        ttk.Label(upd_row, textvariable=self.update_status).pack(side="left", padx=(4, 12))
        ttk.Button(upd_row, text="Check for Update", command=self._check_update_thread).pack(side="left")
        ttk.Checkbutton(upd_row, text="Download update if available", variable=self.download_update).pack(side="left", padx=12)

        # ── File type skip ──
        skip_frame = ttk.LabelFrame(main, text="Files to Skip Converting", padding=8)
        skip_frame.pack(fill="x", pady=4)
        for val, (label, _) in SKIP_OPTIONS.items():
            ttk.Radiobutton(skip_frame, text=f"{val}) {label}", variable=self.skip_var, value=val).pack(anchor="w")

        # ── Action buttons ──
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=8)
        self.convert_btn = ttk.Button(btn_frame, text="Start Conversion", style="Accent.TButton",
                                      command=self._start_conversion)
        self.convert_btn.pack(side="left")
        ttk.Button(btn_frame, text="Open Output Folder", command=self._open_output).pack(side="left", padx=8)

        # ── Log ──
        log_frame = ttk.LabelFrame(main, text="Conversion Log", padding=4)
        log_frame.pack(fill="both", expand=True, pady=(4, 0))
        self.log = scrolledtext.ScrolledText(log_frame, bg="#11111b", fg="#a6e3a1",
                                             font=("Consolas", 9), relief="flat", state="disabled",
                                             wrap="word")
        self.log.pack(fill="both", expand=True)

    # ── Logging ──────────────────────────────────────────────────

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    # ── Directory helpers ────────────────────────────────────────

    def _auto_detect_ps3_game(self):
        default = os.path.join(self.script_dir, "PS3_GAME")
        if os.path.isdir(default):
            self.ps3_game_dir.set(default)
            self._detect_game()

    def _browse_dir(self):
        path = filedialog.askdirectory(title="Select PS3_GAME Folder")
        if path:
            self.ps3_game_dir.set(path)
            self._detect_game()

    # ── PARAM.SFO parsing ───────────────────────────────────────

    def _read_sfo(self, field):
        sfo = os.path.join(self.ps3_game_dir.get(), "PARAM.SFO")
        if not os.path.isfile(sfo):
            return None
        try:
            out = subprocess.check_output([self._tool("sfoprint.exe"), sfo, field],
                                          stderr=subprocess.DEVNULL, cwd=self.script_dir)
            text = out.decode("utf-8", errors="replace").strip()
            if ":" in text:
                return text.split(":", 1)[1].strip()
            return text
        except Exception:
            return None

    def _detect_game(self):
        ps3_dir = self.ps3_game_dir.get()
        if not ps3_dir or not os.path.isdir(ps3_dir):
            messagebox.showerror("Error", "PS3_GAME directory not found.")
            return
        sfo = os.path.join(ps3_dir, "PARAM.SFO")
        if not os.path.isfile(sfo):
            messagebox.showerror("Error", "PARAM.SFO not found in the selected directory.")
            return

        title = self._read_sfo("TITLE") or "Unknown"
        title_id = self._read_sfo("TITLE_ID") or "Unknown"
        version = self._read_sfo("VERSION") or "--"
        app_ver = self._read_sfo("APP_VER") or "--"

        self.game_title.set(title)
        self.disc_title_id.set(title_id)
        self.game_version.set(version)
        self.app_version.set(app_ver)

        prefix = title_id[:4].upper()
        number = title_id[4:] if len(title_id) > 4 else "00000"
        converted = TITLE_ID_MAP.get(prefix, "NPXX") + number
        self.converted_id.set(converted)
        self.custom_id.set("")
        self.update_status.set("Not checked")
        self.update_available = False
        self.update_url = ""

        self._log(f"Detected: {title} [{title_id}] v{version}")
        self._log(f"Suggested conversion ID: {converted}")

    # ── Update check ─────────────────────────────────────────────

    def _check_update_thread(self):
        threading.Thread(target=self._check_update, daemon=True).start()

    def _check_update(self):
        title_id = self.disc_title_id.get()
        if title_id == "--":
            self._log("Detect a game first.")
            return
        url = f"https://a0.ww.np.dl.playstation.net/tpl/np/{title_id}/{title_id}-ver.xml"
        self._log(f"Checking update: {url}")
        self.update_status.set("Checking...")
        try:
            xml_path = os.path.join(self.script_dir, "temp", f"{title_id}.xml")
            os.makedirs(os.path.dirname(xml_path), exist_ok=True)
            subprocess.check_output([
                self._tool("wget.exe"), "--no-check-certificate",
                '--user-agent="Mozilla/5.0 (PLAYSTATION 3; 4.81)"',
                "-O", xml_path, url
            ], stderr=subprocess.DEVNULL, cwd=self.script_dir)

            if not os.path.isfile(xml_path) or os.path.getsize(xml_path) == 0:
                self.update_status.set("No update available")
                self.update_available = False
                self._log("No update XML found.")
                return

            xml_tool = self._tool("xml.exe")
            try:
                ver = subprocess.check_output([xml_tool, "sel", "-t",
                    "-m", "/titlepatch/tag/package", "-v", "@version", xml_path],
                    stderr=subprocess.DEVNULL, cwd=self.script_dir).decode().strip()
                url_out = subprocess.check_output([xml_tool, "sel", "-t",
                    "-m", "/titlepatch/tag/package", "-v", "@url", xml_path],
                    stderr=subprocess.DEVNULL, cwd=self.script_dir).decode().strip()
                size_raw = subprocess.check_output([xml_tool, "sel", "-t",
                    "-m", "/titlepatch/tag/package", "-v", "@size", xml_path],
                    stderr=subprocess.DEVNULL, cwd=self.script_dir).decode().strip()
            except Exception:
                self.update_status.set("No update available")
                self.update_available = False
                self._log("Could not parse update XML.")
                return

            if url_out:
                size_mb = ""
                try:
                    size_mb = f" ({int(size_raw) / (1024*1024):.1f} MB)"
                except Exception:
                    pass
                self.update_url = url_out
                self.update_available = True
                self.update_status.set(f"v{ver} available{size_mb}")
                self._log(f"Update found: v{ver}{size_mb}")
            else:
                self.update_status.set("No update available")
                self.update_available = False
        except Exception as e:
            self.update_status.set("Check failed")
            self._log(f"Update check failed: {e}")

    # ── Conversion ───────────────────────────────────────────────

    def _get_game_id(self):
        custom = self.custom_id.get().strip()
        return custom if custom else self.converted_id.get()

    def _start_conversion(self):
        if self.converting:
            return
        ps3_dir = self.ps3_game_dir.get()
        if not ps3_dir or not os.path.isdir(ps3_dir):
            messagebox.showerror("Error", "Select a valid PS3_GAME directory first.")
            return
        if not os.path.isfile(os.path.join(ps3_dir, "PARAM.SFO")):
            messagebox.showerror("Error", "PARAM.SFO not found.")
            return
        game_id = self._get_game_id()
        if not game_id or game_id == "NPXX00000":
            messagebox.showerror("Error", "Invalid game ID.")
            return
        self.converting = True
        self.convert_btn.configure(state="disabled")
        threading.Thread(target=self._run_conversion, args=(ps3_dir, game_id), daemon=True).start()

    def _run_conversion(self, ps3_dir, game_id):
        try:
            self._log("=" * 60)
            self._log(f"Starting conversion: {game_id}")
            self._log("=" * 60)

            root = self.script_dir
            out_dir = os.path.join(root, game_id)
            lic_dir = os.path.join(out_dir, "LICDIR")
            os.makedirs(lic_dir, exist_ok=True)

            # Download update
            if self.update_available and self.download_update.get():
                self._log("Downloading update package...")
                upd_dir = os.path.join(root, "temp", "update")
                os.makedirs(upd_dir, exist_ok=True)
                fname = self.update_url.rsplit("/", 1)[-1] if self.update_url else "update.pkg"
                try:
                    subprocess.check_output([
                        self._tool("wget.exe"), "--no-check-certificate",
                        '--user-agent="Mozilla/5.0 (PLAYSTATION 3; 4.81)"',
                        "-O", os.path.join(upd_dir, fname), self.update_url
                    ], stderr=subprocess.DEVNULL, cwd=root)
                    self._log(f"Downloaded: {fname}")
                except Exception as e:
                    self._log(f"Update download failed: {e}")

            # Copy TROPDIR and base files
            self._log("Copying base game files...")
            trop_src = os.path.join(ps3_dir, "TROPDIR")
            if os.path.isdir(trop_src):
                shutil.copytree(trop_src, os.path.join(out_dir, "TROPDIR"), dirs_exist_ok=True)

            for item in os.listdir(ps3_dir):
                src = os.path.join(ps3_dir, item)
                dst = os.path.join(out_dir, item)
                if item == "TROPDIR":
                    continue
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

            # Copy skipped file types directly
            skip_idx = self.skip_var.get()
            skip_exts = SKIP_OPTIONS[skip_idx][1]
            self._log(f"Skipping conversion for: {SKIP_OPTIONS[skip_idx][1] or 'none'}")

            # Build file list for conversion
            usrdir = os.path.join(ps3_dir, "USRDIR")
            files_to_convert = []
            if os.path.isdir(usrdir):
                for dirpath, _, filenames in os.walk(usrdir):
                    for fn in filenames:
                        full = os.path.join(dirpath, fn)
                        ext = os.path.splitext(fn)[1].lower()
                        if fn.upper() == "EBOOT.BIN":
                            continue
                        if ext in skip_exts:
                            continue
                        rel = os.path.relpath(full, ps3_dir)
                        files_to_convert.append(rel)

            total = len(files_to_convert) + 1  # +1 for EBOOT.BIN
            self._log(f"Files to convert: {total}")

            # Convert EBOOT.BIN
            eboot_src = os.path.join(ps3_dir, "USRDIR", "EBOOT.BIN")
            eboot_dst = os.path.join(out_dir, "USRDIR", "EBOOT.BIN")
            if os.path.isfile(eboot_src):
                self._log("Converting EBOOT.BIN...")
                self._run_make_npdata(eboot_src, eboot_dst)

            # Convert other files
            for i, rel in enumerate(files_to_convert):
                src = os.path.join(ps3_dir, rel)
                dst = os.path.join(out_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                self._log(f"[{i+1}/{len(files_to_convert)}] Converting: {rel}")
                self._run_make_npdata(src, dst)

            # License handling
            disc_lic = os.path.join(ps3_dir, "LICDIR", "LIC.DAT")
            npd_lic = os.path.join(out_dir, "LICDIR", "LIC.EDAT")
            license_ok = os.path.isfile(disc_lic)

            if not license_ok:
                self._log("No LIC.DAT found - launching KDW License Generator...")
                self._log("In KDW app: press C, then 1, then ENTER to create license.")
                kdw_dir = os.path.join(self.bin_path, "kdw-licdat")
                kdw_src_sfo = os.path.join(ps3_dir, "PARAM.SFO")
                kdw_dst_sfo = os.path.join(kdw_dir, "GAMES", "CREATE_NEW_LICENSE", "PS3_GAME", "PARAM.SFO")
                try:
                    shutil.copy2(kdw_src_sfo, kdw_dst_sfo)
                except Exception:
                    pass
                subprocess.Popen([os.path.join(kdw_dir, "kdw_license_gen.exe")], cwd=kdw_dir)
                messagebox.showinfo("License Required",
                    "The KDW License Generator has been opened.\n\n"
                    "Press C, then 1, then ENTER to create a new LIC.DAT.\n\n"
                    "Click OK here when done.")
                new_lic = os.path.join(kdw_dir, "GAMES", "CREATE_NEW_LICENSE", "PS3_GAME", "LICDIR", "LIC.DAT")
                if os.path.isfile(new_lic):
                    out_lic_dir = os.path.join(out_dir, "LICDIR")
                    os.makedirs(out_lic_dir, exist_ok=True)
                    shutil.copy2(new_lic, os.path.join(out_lic_dir, "LIC.DAT"))
                    license_ok = True
                    self._log("License created and copied.")
                else:
                    self._log("WARNING: LIC.DAT still not found after KDW.")

            if license_ok:
                self._log("Creating NPDRM license (LIC.EDAT)...")
                lic_dat_path = os.path.join(out_dir, "LICDIR", "LIC.DAT")
                content_id = f"EP9000-{game_id}_00-0000000000000001"
                try:
                    subprocess.check_output([
                        self._tool("make_npdata.exe"), "-e",
                        lic_dat_path, npd_lic,
                        "1", "1", "3", "0", "16", "3", "00", content_id, "1"
                    ], stderr=subprocess.STDOUT, cwd=root)
                    self._log("LIC.EDAT created successfully.")
                except subprocess.CalledProcessError as e:
                    self._log(f"LIC.EDAT creation output: {e.output.decode(errors='replace')}")

            # Create marker file
            marker = os.path.join(out_dir, "USRDIR", f"EP9000-{game_id}_00-0000000000000001.txt")
            with open(marker, "w") as f:
                f.write("")

            self._log("=" * 60)
            self._log("CONVERSION COMPLETE!")
            self._log(f"Output: {out_dir}")
            self._log("=" * 60)

        except Exception as e:
            self._log(f"ERROR: {e}")
            import traceback
            self._log(traceback.format_exc())
        finally:
            self.converting = False
            self.after(0, lambda: self.convert_btn.configure(state="normal"))

    def _run_make_npdata(self, src, dst):
        try:
            subprocess.check_output([
                self._tool("make_npdata.exe"), "-e", src, dst,
                "0", "1", "3", "0", "16"
            ], stderr=subprocess.STDOUT, cwd=self.script_dir)
        except subprocess.CalledProcessError:
            pass

    def _open_output(self):
        game_id = self._get_game_id()
        out = os.path.join(self.script_dir, game_id)
        if os.path.isdir(out):
            os.startfile(out)
        else:
            messagebox.showinfo("Info", f"Output folder does not exist yet:\n{out}")


if __name__ == "__main__":
    app = PS3ConverterGUI()
    app.mainloop()
