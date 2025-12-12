"""
    This is designed to be an app that helps with working out

    Main features will be:
        - Selecting what body area the user wants to work out
        - Loading what workout, sets, reps, and weight the user could use
        - Set personal records(prs) and update them using a database

    Want to implement:
        - Track previous workouts
"""

import tkinter as tk
import json
import random
import sqlite3

# Connect to database
conn = sqlite3.connect("workout_data.db")
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS personal_records (
    exercise TEXT PRIMARY KEY,
    muscle_group TEXT,
    pr_weight REAL
)
""")
conn.commit()

# Create the main window
root = tk.Tk()
root.title("Workout App")

# Read JSON file
with open("workouts.json") as file:
    data = json.load(file)

# Needed to check if the CheckButtons are checked or not
muscle_vars = {
    "Forearms": tk.BooleanVar(),
    "Biceps": tk.BooleanVar(),
    "Triceps": tk.BooleanVar(),
    "Chest": tk.BooleanVar(),
    "Back": tk.BooleanVar(),
    "Legs": tk.BooleanVar()
}

num_workouts_label = tk.Label(root, text="How many workouts per muscle area? ")
num_workouts_label.grid(row=3, column=1, columnspan=2)
num_workouts = tk.Entry(root, width=3)
num_workouts.grid(row=3, column=3, sticky="w")

def display_workout():
    """
        This function will take what body area the user wants to workout
        Find the JSON data that correlates with that body area
        And will display the workout, sets, and reps that is recommended for the user
    """
    output_box.delete("1.0", tk.END) # Clears item if unchecked

    selected_areas = [muscle for muscle, item in muscle_vars.items() if item.get()] # Gets what buttons are checked and acts as an array

    # Try to read number of workouts if user hasn't entered any, display all items
    try:
        num_text = num_workouts.get()
        if num_text.strip() == "":
            num = None  
        else:
            num = int(num_text)
            if num < 1:
                raise ValueError
    except ValueError:
        output_box.insert(tk.END, "Enter a valid number, otherwise leave blank for all workouts")
        return

    # Display
    for area in selected_areas:
        output_box.insert(tk.END, f"----- {area} Workout -----\n")
        exercises = data[area]
        
        if num == None: 
            workouts = exercises # Display all exercises
        else:
            workouts = random.sample(exercises, k=min(num, len(exercises))) # Selects random exercises

        for workout in workouts:
            exercise = workout["exercise"]
            sets = workout["sets"]
            reps = workout["reps"]

            # Check for if the workout has a "weight" amount
            is_bodyweight = ("weight" not in workout) or workout["weight"] in ["Bodyweight", "", None]

            # Get PR if it exists
            cursor.execute("SELECT pr_weight FROM personal_records WHERE exercise = ?", (exercise,))
            result = cursor.fetchone()

            if result and result[0] > 0:
                # Calculate recommended weight based off PR
                pr = result[0]
                percent_low = 0.60
                percent_high = 0.80
                weight_low = round(pr * percent_low)
                weight_high = round(pr * percent_high)
                weight_text = f"{weight_low}-{weight_high} lbs"
            else:
                weight_text = workout["weight"]

            if is_bodyweight:
                # Display workouts without weight
                output_box.insert(tk.END, f"{exercise} — {sets} x {reps}\n")
            else:
                # Display workouts with weight
                output_box.insert(tk.END, f"{exercise} — {sets} x {reps} @ {weight_text}\n")

def save_pr():
    """
        This function, the user will select the workout they want to save a new PR for
        Enter in the PR in lbs. and save the PR
    """
    selected_text = output_box.get("sel.first", "sel.last")
    if not selected_text:
        output_box.insert(tk.END, "\nSelect an exercise line first.\n")
        return

    try:
        pr_value = float(pr_entry.get())
    except:
        output_box.insert(tk.END, "\nEnter a valid number for PR.\n")
        return

    # Extract exercise name from selected text
    exercise_name = selected_text.split("—")[0].strip()

    # Find the muscle group for DB storage
    muscle_group = None
    for area, workouts in data.items():
        for w in workouts:
            if w["exercise"] == exercise_name:
                muscle_group = area
                break

    cursor.execute("""
        INSERT INTO personal_records (exercise, muscle_group, pr_weight)
        VALUES (?, ?, ?)
        ON CONFLICT(exercise) DO UPDATE SET pr_weight = excluded.pr_weight
    """, (exercise_name, muscle_group, pr_value))
    conn.commit()

    output_box.insert(tk.END, f"\nPR saved for {exercise_name}: {pr_value}\n")


# Body Area Options
choice_text = tk.Label(root, text="Choose what area you want to workout:")
choice_text.grid(row=4, column=1, columnspan=3, padx=5, pady=5)

# Top row of Buttons
forearms_button = tk.Checkbutton(root, text="Forearms", variable=muscle_vars["Forearms"], command= display_workout)
forearms_button.grid(row=6, column=1, padx=10, pady=10, sticky="w")
biceps_button = tk.Checkbutton(root, text="Biceps", variable=muscle_vars["Biceps"], command= display_workout)
biceps_button.grid(row=6, column=2, padx=10, pady=10, sticky="w")
triceps_button = tk.Checkbutton(root, text="Triceps", variable=muscle_vars["Triceps"], command= display_workout)
triceps_button.grid(row=6, column=3, padx=10, pady=10, sticky="w")
# Botton Row of Buttons
chest_button = tk.Checkbutton(root, text="Chest", variable=muscle_vars["Chest"], command= display_workout)
chest_button.grid(row=5,column=1, padx=10, pady=10, sticky="w")
back_button = tk.Checkbutton(root, text="Back", variable=muscle_vars["Back"], command= display_workout)
back_button.grid(row=5, column=2, padx=10, pady=10, sticky="w")
legs_button = tk.Checkbutton(root, text="Legs", variable=muscle_vars["Legs"], command= display_workout)
legs_button.grid(row=5, column=3, padx=10, pady=10, sticky="w")

# Output text box
output_box = tk.Text(root, width=60, height=12)
output_box.grid(row=7, column=1, columnspan=3, padx=10, pady=10)

pr_label = tk.Label(root, text="Enter PR for selected exercise:")
pr_label.grid(row=8, column=1, columnspan=2, sticky="e")

pr_entry = tk.Entry(root, width=6)
pr_entry.grid(row=8, column=3, sticky="w")

save_pr_button = tk.Button(root, text="Save PR", command=lambda: save_pr())
save_pr_button.grid(row=9, column=2, padx=5)

# Run App
root.mainloop()