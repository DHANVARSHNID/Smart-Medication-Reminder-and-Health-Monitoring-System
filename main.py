import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import time
import threading
from datetime import datetime
import winsound
import serial

# Set Bluetooth COM port
BT_PORT = "COM9"  # Change this to your actual port
BAUD_RATE = 9600

try:
    bt_serial = serial.Serial(BT_PORT, BAUD_RATE, timeout=1)
except:
    bt_serial = None
    print("Bluetooth device not connected!")

SCHEDULE_FILE = "medication_schedule.json"
LOG_FILE = "medication_log.json"

# Load and save medication schedule
def load_schedule():
    try:
        with open(SCHEDULE_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"medications": []}

def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as file:
        json.dump(schedule, file, indent=4)

# Load and save medication log
def load_log():
    try:
        with open(LOG_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"logs": []}

def save_log(log_data):
    with open(LOG_FILE, "w") as file:
        json.dump(log_data, file, indent=4)

# Read Pulse Rate & Heart Rate from Bluetooth
def read_vitals():
    if bt_serial:
        bt_serial.flush()
        try:
            data = bt_serial.readline().decode().strip()
            if "," in data:
                pulse_rate, heart_rate = data.split(",")
                pulse_rate = int(pulse_rate) if pulse_rate.isdigit() else 0
                heart_rate = int(heart_rate) if heart_rate.isdigit() else 0
                return pulse_rate, heart_rate
        except:
            pass
    return 0, 0  # Default values if Bluetooth is disconnected or data is invalid

# Check if vitals are normal
def check_vitals(pulse_rate, heart_rate):
    if not isinstance(pulse_rate, int) or not isinstance(heart_rate, int):
        return "Unknown", "Unknown"

    pulse_status = "Normal" if 60 <= pulse_rate <= 100 else "Abnormal"
    heart_status = "Normal" if 60 <= heart_rate <= 100 else "Abnormal"
    return pulse_status, heart_status

# Add medication
def add_medication():
    name = simpledialog.askstring("Medication Name", "Enter medication name:")
    if not name:
        return

    dosage = simpledialog.askstring("Dosage", f"Enter dosage for {name}:")
    if not dosage:
        return

    schedule = simpledialog.askstring("Schedule", "Enter times (comma-separated, e.g., 08:00, 14:00):")
    if not schedule:
        return

    times = [time.strip() for time in schedule.split(",")]
    data = load_schedule()
    data["medications"].append({"name": name, "dosage": dosage, "schedule": times})
    save_schedule(data)
    messagebox.showinfo("Success", f"{name} has been added successfully!")
    display_schedule()

# Delete medication
def delete_medication():
    data = load_schedule()
    if not data["medications"]:
        messagebox.showinfo("Delete Medication", "No medications to delete.")
        return
    
    med_names = [med["name"] for med in data["medications"]]
    med_to_delete = simpledialog.askstring("Delete Medication", f"Enter medication name to delete: {', '.join(med_names)}")
    if not med_to_delete:
        return
    
    data["medications"] = [med for med in data["medications"] if med["name"] != med_to_delete]
    save_schedule(data)
    messagebox.showinfo("Success", f"{med_to_delete} has been deleted successfully!")
    display_schedule()

# Display medication schedule
def display_schedule():
    data = load_schedule()
    schedule_text.delete("1.0", tk.END)
    if not data["medications"]:
        schedule_text.insert(tk.END, "No medications scheduled.\n")
    else:
        for med in data["medications"]:
            schedule_text.insert(tk.END, f"\ud83d\udccc {med['name']} ({med['dosage']})\n")
            schedule_text.insert(tk.END, f"   Times: {', '.join(med['schedule'])}\n\n")

# Display medication log
def display_log():
    log_data = load_log()
    log_text.delete("1.0", tk.END)
    if not log_data["logs"]:
        log_text.insert(tk.END, "No medication has been taken yet.\n")
    else:
        for log in log_data["logs"]:
            log_text.insert(tk.END, f"\u2705 {log['name']} ({log['dosage']}) - Taken at {log['timestamp']}\n")
            log_text.insert(tk.END, f"   Pulse Rate: {log['pulse_rate']} bpm ({log['pulse_status']}), Heart Rate: {log['heart_rate']} bpm ({log['heart_status']})\n\n")

# Check medication schedule & trigger reminders
def check_reminders():
    while True:
        current_time = datetime.now().strftime("%H:%M")
        data = load_schedule()
        for med in data["medications"]:
            if current_time in med["schedule"]:
                show_alert(med["name"], med["dosage"])
        time.sleep(60)

# Show reminder popup with Pulse Rate & Heart Rate
def show_alert(med_name, dosage):
    pulse_rate, heart_rate = read_vitals()
    pulse_status, heart_status = check_vitals(pulse_rate, heart_rate)

    result = messagebox.askyesno(
        "Medication Reminder",
        f"Time to take {med_name} ({dosage})!\n\nPulse Rate: {pulse_rate} bpm ({pulse_status})\nHeart Rate: {heart_rate} bpm ({heart_status})\n\nHave you taken it?"
    )

    if result:
        log_data = load_log()
        log_data["logs"].append({
            "name": med_name,
            "dosage": dosage,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pulse_rate": pulse_rate,
            "heart_rate": heart_rate,
            "pulse_status": pulse_status,
            "heart_status": heart_status
        })
        save_log(log_data)
        display_log()
    
    winsound.Beep(1000, 500)

# GUI Setup
root = tk.Tk()
root.title("Medication Reminder & Health Monitor")
root.geometry("500x500")

schedule_text = tk.Text(root, height=10, width=60, bg="pink")
schedule_text.pack()
btn_add = tk.Button(root, text="Add Medication", command=add_medication)
btn_add.pack()
btn_delete = tk.Button(root, text="Delete Medication", command=delete_medication)
btn_delete.pack()
log_text = tk.Text(root, height=10, width=60, bg="pink")
log_text.pack()

# Start reminder thread
reminder_thread = threading.Thread(target=check_reminders, daemon=True)
reminder_thread.start()

root.mainloop()