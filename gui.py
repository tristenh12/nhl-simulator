import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import pandas as pd
import random
from sim_engine import simulate_season, build_dataframe, get_division
from playoff import simulate_playoffs, draw_bracket_canvas
from tkinter import scrolledtext
from functools import partial
from collections import defaultdict

class FullSimPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="TFrame")

        self.season_df = pd.read_csv("C:/Users/Tristan/Documents/nhl_sim/data/teams_alignment_complete.csv")
        self.available_seasons = sorted(self.season_df["Season"].unique(), reverse=True)
        self.default_season = self.available_seasons[0]
        self.all_teams = sorted(self.season_df[self.season_df["Season"] == self.default_season]["Team"].unique())
        self.unique_teams = sorted(self.season_df["Team"].unique())
        self.team_slots = []

        # Frames
        self.home_frame = ttk.Frame(self)
        self.home_frame.pack(fill="both", expand=True)

        self.results_frame = ttk.Frame(self)
        self.results_frame.pack_forget()

        self.text_frame = ttk.Frame(self.results_frame)
        self.text_frame.pack(fill="both", expand=True)

        self.output_text = scrolledtext.ScrolledText(self.text_frame, wrap=ttk.WORD, width=140, height=35, font=("Courier", 10))
        self.output_text.pack(fill="both", expand=True, pady=10)

        self.back_btn = ttk.Button(self.results_frame, text="🏠 Back to Home", command=self.go_home)
        self.back_btn.pack(pady=10)

        self.view_dropdown = ttk.Combobox(self.results_frame, values=["By Division", "By Conference", "Entire League", "Playoffs"], state="readonly")
        self.view_dropdown.set("By Division")
        self.view_dropdown.pack(pady=5)
        self.view_dropdown.bind("<<ComboboxSelected>>", lambda e: self.sort_view(self.view_dropdown.get()))

        self.bracket_frame = ttk.Frame(self.results_frame)
        self.bracket_frame.pack_forget()
        self.bracket_canvas_holder = [None]

        self.setup_styles()
        self.setup_layout()


    def setup_styles(self):
        style = ttk.Style()
        style.configure("TButton", background="#2e2e2e", foreground="white", padding=6)
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Helvetica", 14))

    def setup_layout(self):
        frame = ttk.Frame(self.home_frame, padding="20 20 20 20")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="\U0001F3C2 SIM ENGINE \U0001F3C2").pack(pady=10)

        self.canvas_frame = ttk.Frame(frame)
        self.canvas_frame.pack(fill="both", expand=True)

        canvas = ttk.Canvas(self.canvas_frame, bg="#1e1e1e")
        scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("all", width=e.width))

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.editor_frame = ttk.LabelFrame(scrollable_frame, text="\U0001F4CB Custom League Editor", padding=10,)
        self.editor_frame.pack(fill="x", padx=60, pady=10)
    


        self.control_frame = ttk.Frame(scrollable_frame)
        self.control_frame.pack(pady=10)

        self.season_selector = ttk.Combobox(self.control_frame, values=self.available_seasons, width=10, state="readonly")
        self.season_selector.set(self.default_season)

        self.team_selector = ttk.Combobox(self.control_frame, values=self.unique_teams, width=25, state="readonly")
        self.team_selector.set(self.unique_teams[0])

        self.create_team_slots()
        self.create_controls()
   
    def update_season_options(self, combo, team_name):
        team_seasons = self.season_df[self.season_df["Team"] == team_name]["Season"].unique()
        combo["values"] = sorted(team_seasons, reverse=True)
        if team_seasons.size > 0:
            combo.set(team_seasons[0])

    def create_team_slots(self):
        self.left_column = ttk.Frame(self.editor_frame)
        self.left_column.pack(side="left", expand=True, padx=(80, 40), anchor="n")

        self.right_column = ttk.Frame(self.editor_frame)
        self.right_column.pack(side="right", expand=True, padx=(40, 80), anchor="n")

        for i in range(32):
            parent = self.left_column if i < 16 else self.right_column
            slot_frame = ttk.Frame(parent)
            slot_frame.pack(anchor="center", pady=2)

            slot_number = f"{i+1:02}"
            ttk.Label(slot_frame, text=f"{slot_number}:", width=5, anchor="w").pack(side="left")

            team_cb = ttk.Combobox(slot_frame, values=self.all_teams, width=30)
            default_team = self.all_teams[i % len(self.all_teams)]
            team_cb.set(default_team)
            team_cb.pack(side="left", padx=5)

            season_cb = ttk.Combobox(slot_frame, width=10)
            self.update_season_options(season_cb, default_team)
            season_cb.set(self.default_season)
            season_cb.pack(side="left", padx=5)

            team_cb.config(state="disabled")
            season_cb.config(state="disabled")

            edit_btn = ttk.Button(slot_frame, text="Edit")
            edit_btn.pack(side="left", padx=5)

            def toggle(btn=edit_btn, t_cb=team_cb, s_cb=season_cb):
                self.toggle_edit(btn, t_cb, s_cb)

            edit_btn.config(command=toggle)
            self.team_slots.append((team_cb, season_cb, edit_btn))

        self.edit_all_state = {"editing": False}

    def create_controls(self):
        control_frame = ttk.Frame(self.home_frame)
        control_frame.pack(pady=10)

        # Season controls
        season_frame = ttk.Frame(control_frame)
        season_frame.pack(side="left", padx=5)

        ttk.Label(season_frame, text="Season:").pack(side="left")
        self.season_selector = ttk.Combobox(season_frame, values=self.available_seasons, width=10, state="readonly")
        self.season_selector.set(self.default_season)
        self.season_selector.pack(side="left", padx=(5, 0))
        ttk.Button(season_frame, text="Apply Year", command=self.fill_full_season).pack(side="left", padx=5)

        # Team controls
        team_frame = ttk.Frame(control_frame)
        team_frame.pack(side="left", padx=5)

        ttk.Label(team_frame, text="Team:").pack(side="left")
        self.team_selector = ttk.Combobox(team_frame, values=self.unique_teams, width=25, state="readonly")
        self.team_selector.set(self.unique_teams[0])
        self.team_selector.pack(side="left", padx=(5, 0))
        ttk.Button(team_frame, text="Same Team by Year", command=self.fill_all_one_team).pack(side="left", padx=5)

        # Other buttons
        self.edit_all_btn = ttk.Button(control_frame, text="Edit All", command=self.toggle_all_edit)
        self.edit_all_btn.pack(side="left", padx=5)

        ttk.Button(control_frame, text="\U0001F331 Reset Default", command=self.reset_all).pack(side="left", padx=5)
        ttk.Button(control_frame, text="♻ Randomize", command=self.fill_random).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✅ Preview League", command=self.preview_league).pack(side="left", padx=5)
        ttk.Button(control_frame, text="\U0001F3D2 Run Simulation", command=self.run_simulation).pack(side="left", padx=5)

    def fill_random(self):
        for team_cb, season_cb, _ in self.team_slots:
            team_cb.config(state="normal")
            season_cb.config(state="normal")
            team = random.choice(self.season_df["Team"].unique())
            team_cb.set(team)
            self.update_season_options(season_cb, team)
            season_cb.set(random.choice(self.season_df[self.season_df["Team"] == team]["Season"].tolist()))
            team_cb.config(state="disabled")
            season_cb.config(state="disabled")

    def fill_full_season(self):
        selected_season = self.season_selector.get()
        if not selected_season:
            return

        teams = sorted(self.season_df[self.season_df["Season"] == selected_season]["Team"].unique())

        for i, (team_cb, season_cb, _) in enumerate(self.team_slots):
            if i < len(teams):
                team = teams[i]
                team_cb.config(state="normal")
                season_cb.config(state="normal")
                team_cb.set(team)
                self.update_season_options(season_cb, team)
                season_cb.set(selected_season)
                team_cb.config(state="disabled")
                season_cb.config(state="disabled")
            else:
                team_cb.set("")
                season_cb.set("")
                team_cb.config(state="disabled")
                season_cb.config(state="disabled")

    def reset_all(self):
        self.season_selector.set(self.default_season)
        self.fill_full_season()

    def fill_all_one_team(self):
        selected_team = self.team_selector.get()
        if not selected_team:
            return

        all_years = sorted(self.season_df[self.season_df["Team"] == selected_team]["Season"].unique(), reverse=True)

        for i, (team_cb, season_cb, _) in enumerate(self.team_slots):
            if i < len(all_years):
                year = all_years[i]
                team_cb.config(state="normal")
                season_cb.config(state="normal")
                team_cb.set(selected_team)
                self.update_season_options(season_cb, selected_team)
                season_cb.set(year)
                team_cb.config(state="disabled")
                season_cb.config(state="disabled")
            else:
                team_cb.set("Unavailable")
                season_cb.set("Unavailable")
                team_cb.config(state="disabled")
                season_cb.config(state="disabled")

    def toggle_edit(self, btn, team_cb, season_cb):
        if not hasattr(btn, "editing") or not btn.editing:
            team_cb.config(state="normal")
            season_cb.config(state="normal")
            btn.config(text="Confirm")
            btn.editing = True
        else:
            team_cb.config(state="disabled")
            season_cb.config(state="disabled")
            btn.config(text="Edit")
            btn.editing = False

    def show_result_window(self):
        self.home_frame.pack_forget()
        self.results_frame.pack(fill="both", expand=True)

    def go_home(self):
        self.results_frame.pack_forget()
        self.home_frame.pack(fill="both", expand=True)

    def preview_league(self):
        selected_teams = []
        for team_cb, season_cb, _ in self.team_slots:
            team = team_cb.get()
            season = season_cb.get()
            if team and season:
                selected_teams.append((team, season))

        self.show_result_window()
        self.view_dropdown.pack_forget()
        self.output_text.delete("1.0", ttk.END)
        self.output_text.tag_configure("center", justify="center")

        if len(selected_teams) != 32:
            self.output_text.insert(ttk.END, "⚠️ Please fill all 32 team slots before previewing.\n\n")

        divisions = {
            "Atlantic": [],
            "Metropolitan": [],
            "Central": [],
            "Pacific": []
        }

        for team, season in selected_teams:
            row = self.season_df[(self.season_df["Team"] == team) & (self.season_df["Season"] == season)]
            if not row.empty:
                div = row.iloc[0]["Division"]
                if div not in divisions:
                    div = min(divisions, key=lambda d: len(divisions[d]))
            else:
                div = min(divisions, key=lambda d: len(divisions[d]))

            divisions[div].append(f"{team} ({season})")

        self.output_text.insert(ttk.END, "=== Custom League Preview (By Division) ===\n\n", "center")
        for div_name, teams in divisions.items():
            self.output_text.insert(ttk.END, f"--- {div_name} ---\n", "center")
            for team_entry in teams:
                self.output_text.insert(ttk.END, f"{team_entry}\n", "center")
            self.output_text.insert(ttk.END, "\n")
    
    def toggle_all_edit(self):
        for team_cb, season_cb, btn in self.team_slots:
            if not self.edit_all_state["editing"]:
                team_cb.config(state="normal")
                season_cb.config(state="normal")
                btn.config(text="Confirm")
                btn.editing = True
            else:
                team_cb.config(state="disabled")
                season_cb.config(state="disabled")
                btn.config(text="Edit")
                btn.editing = False

        self.edit_all_btn.config(text="Confirm All" if not self.edit_all_state["editing"] else "Edit All")
        self.edit_all_state["editing"] = not self.edit_all_state["editing"]

    def sort_view(self, mode):
        if not hasattr(self, "last_df") or self.output_text is None:
            return

        self.bracket_frame.pack_forget()
        self.text_frame.pack(fill="both", expand=True)
        self.output_text.delete("1.0", ttk.END)
        self.output_text.tag_configure("center", justify="center")
        self.view_dropdown.pack(pady=5)

        if self.bracket_canvas_holder[0]:
            self.bracket_canvas_holder[0].destroy()
            self.bracket_canvas_holder[0] = None

        if mode == "By Division":
            self.output_text.insert(ttk.END, "=== NHL STANDINGS (By Division) ===\n", "center")
            for div in self.last_df["Division"].unique():
                div_df = self.last_df[self.last_df["Division"] == div].sort_values(by=["PTS", "Win%"], ascending=[False, False])
                self.output_text.insert(ttk.END, f"--- {div} ---\n", "center")
                self.output_text.insert(ttk.END, self.format_df(div_df).to_string(index=False) + "\n", "center")
                self.output_text.insert(ttk.END, "\n\n")

        elif mode == "By Conference":
            self.output_text.insert(ttk.END, "=== NHL STANDINGS (By Conference) ===\n", "center")
            for conf in self.last_df["Conference"].unique():
                conf_df = self.last_df[self.last_df["Conference"] == conf].sort_values(by=["PTS", "Win%"], ascending=[False, False])
                self.output_text.insert(ttk.END, f"--- {conf} ---\n", "center")
                self.output_text.insert(ttk.END, self.format_df(conf_df).to_string(index=False) + "\n", "center")
                self.output_text.insert(ttk.END, "\n\n")

        elif mode == "Entire League":
            self.output_text.insert(ttk.END, "=== NHL STANDINGS (Entire League) ===\n", "center")
            league_df = self.last_df.sort_values(by=["PTS", "Win%"], ascending=[False, False])
            self.output_text.insert(ttk.END, self.format_df(league_df).to_string(index=False) + "\n", "center")
            self.output_text.insert(ttk.END, "\n")

        elif mode == "Playoffs":
            self.text_frame.pack_forget()
            self.bracket_frame.pack(fill="both", expand=True)

            if self.bracket_canvas_holder[0]:
                self.bracket_canvas_holder[0].destroy()

            if "Rating" in self.last_df.columns:
                ratings_dict = {row["Team"]: row["Rating"] for _, row in self.last_df.iterrows()}
                bracket = simulate_playoffs(self.last_df, ratings_dict)
                self.bracket_canvas_holder[0] = draw_bracket_canvas(None, self.bracket_frame, bracket, self.season_df)
            else:
                label = ttk.Label(self.bracket_frame, text="Error: 'Rating' column missing from dataframe.", foreground="red")
                label.pack()
                self.bracket_canvas_holder[0] = label

    def format_df(self, df):
        hide_cols = {"rating", "rawteam", "win%", "division", "conference"}
        df = df.drop(columns=[col for col in df.columns if col.strip().lower() in hide_cols], errors='ignore')
        df.columns = [f"{col:^15}" for col in df.columns]
        df = df.astype(str).map(lambda x: f"{x:^15}")
        return df


    def run_simulation(self):
        selected_teams = []
        for team_cb, season_cb, _ in self.team_slots:
            team = team_cb.get()
            season = season_cb.get()
            if team and season and team in self.season_df["Team"].values:
                row = self.season_df[(self.season_df["Team"] == team) & (self.season_df["Season"] == season)]
                if not row.empty:
                    team_key = f"{team} ({season})"
                    selected_teams.append({
                        "Team": team_key,
                        "Season": season,
                        "Division": row.iloc[0]["Division"],
                        "Conference": row.iloc[0]["Conference"],
                        "Rating": row.iloc[0]["Rating"],
                        "RawTeam": team
                    })

        self.go_home()
        self.home_frame.pack_forget()
        self.results_frame.pack(fill="both", expand=True)

        if len(selected_teams) < 10:
            self.output_text.insert("end", "⚠️ Please submit at least 10 teams to run a valid simulation.\n")
            return
        elif len(selected_teams) < 32:
            self.output_text.insert("end", f"⚠️ Only {len(selected_teams)} teams selected. Simulation may be unbalanced.\n\n")

        east_count = sum(1 for t in selected_teams if t["Conference"] == "East")
        west_count = sum(1 for t in selected_teams if t["Conference"] == "West")

        if east_count < 8 or west_count < 8:
            self.output_text.insert("end", f"⚠️ Not enough teams in each conference for full playoffs (East: {east_count}, West: {west_count})\n\n")

        divisions = {"Atlantic": [], "Metropolitan": [], "Central": [], "Pacific": []}
        ratings = {}

        for team in selected_teams:
            div = team["Division"] if team["Division"] in divisions else random.choice(list(divisions.keys()))
            divisions[div].append(team["Team"])
            ratings[team["Team"]] = team["Rating"]

        stats = simulate_season(divisions, ratings)
        df, auto_assigned = build_dataframe(stats, divisions, self.season_df)

        if auto_assigned:
            self.output_text.insert("end", "⚠️ Some teams were auto-assigned to East/West to enable simulation.\n\n")

        self.last_df = df
        self.view_dropdown.set("By Division")
        self.sort_view("By Division")

        control_frame = ttk.Frame(frame)
        control_frame.pack(pady=10)

        ttk.Button(control_frame, text="\U0001F331 Reset Default", command=self.reset_all).pack(side="left", padx=5)

        # Season Controls
        season_frame = ttk.Frame(control_frame)
        season_frame.pack(side="left", padx=5)
        ttk.Label(season_frame, text="Season:").pack(side="left")

        self.season_selector = ttk.Combobox(season_frame, values=self.available_seasons, width=10, state="readonly")
        self.season_selector.set(self.default_season)
        self.season_selector.pack(side="left", padx=(5, 0))
        ttk.Button(season_frame, text="Apply Year", command=self.fill_full_season).pack(side="left", padx=5)

        # Team Controls
        team_frame = ttk.Frame(control_frame)
        team_frame.pack(side="left", padx=5)
        ttk.Label(team_frame, text="Team:").pack(side="left")

        self.team_selector = ttk.Combobox(team_frame, values=self.unique_teams, width=25, state="readonly")
        self.team_selector.set(self.unique_teams[0])
        self.team_selector.pack(side="left", padx=(5, 0))
        ttk.Button(team_frame, text="Same Team by Year", command=self.fill_all_one_team).pack(side="left", padx=5)

        self.edit_all_btn = ttk.Button(control_frame, text="Edit All", command=self.toggle_all_edit)
        self.edit_all_btn.pack(side="left", padx=5)

        ttk.Button(control_frame, text="♻ Randomize", command=self.fill_random).pack(side="left", padx=5)
        ttk.Button(control_frame, text="✅ Preview League", command=self.preview_league).pack(side="left", padx=5)
        ttk.Button(control_frame, text="\U0001F3D2 Run Simulation", command=self.run_simulation).pack(side="left", padx=5)

    def go_home(self):
        self.results_frame.pack_forget()
        self.home_frame.pack(fill="both", expand=True)

    def show_result_window(self):
        self.home_frame.pack_forget()
        self.results_frame.pack(fill="both", expand=True)

if __name__ == "__main__":
    import tkinter as tk
    root = ttk.Window(themename="darkly")
    page = FullSimPage(root)
    page.pack(fill="both", expand=True)
    root.mainloop()
