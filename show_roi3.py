import mss
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import pyautogui
import time
import pygetwindow as gw
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os
import sys
import copy
import threading 

regions = [
 
    {'top': 388, 'left': 757, 'width': 286, 'height': 86, 'name': 'roi1'},
    {'top': 172, 'left': 95, 'width': 180, 'height': 50, 'name': 'roi2'},
    {'top': 318, 'left': 134, 'width': 229, 'height': 45, 'name': 'roi3'},
    {'top': 512, 'left': 216, 'width': 150, 'height': 69, 'name': 'roi4'},
    {'top': 518, 'left': 43, 'width': 150, 'height': 69, 'name': 'roi5'},
    {'top': 705, 'left': 215, 'width': 150, 'height': 69, 'name': 'roi6'},
    {'top': 700, 'left': 36, 'width': 150, 'height': 69, 'name': 'roi7'},
    {'top': 892, 'left': 205, 'width': 150, 'height': 69, 'name': 'roi8'},
    {'top': 895, 'left': 41, 'width': 150, 'height': 69, 'name': 'roi9'},
    {'top': 843, 'left': 864, 'width': 150, 'height': 69, 'name': 'roi10'}



]

selected_roi = None
dragging = False
drag_start = (0, 0)
screen_snapshot = None
capture_process = None
media_player_rect = None  # Stores window position and size

def on_stop_program_button_click():
    """Terminate the entire program."""
    if capture_process:  # Stop the logging process if it's running
        capture_process.terminate()
    root.destroy()  # Close the GUI
    sys.exit()  # Terminate the program


def launch_mission_planner():
    """Launch Mission Planner if not already running."""
    try:
        # Update this path to the actual Mission Planner executable location
        mission_planner_path = r"C:\Program Files (x86)\Mission Planner\MissionPlanner.exe"
        if os.path.exists(mission_planner_path):
            subprocess.Popen(["start", "cmd", "/k", mission_planner_path],shell=True)
            print("Launching Mission Planner...")
            time.sleep(5)  # Wait for Mission Planner to launch
            return True
        else:
            messagebox.showerror("Error", f"Mission Planner not found at: {mission_planner_path}")
            return False
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch Mission Planner: {e}")
        return False
    
def maximize_until_mission_planner():
    """Maximize Mission planner window and record its position."""
    global media_player_rect
    try:
        
        pyautogui.hotkey("win", "tab")
        time.sleep(1.5)
        minimized_windows = [win for win in gw.getAllWindows() if win.isMinimized]
        if minimized_windows:
           print("Minimized Windows:")
           for win in minimized_windows:
              print(f"- {win.title}")
           mission_planner_found = any("Mission Planner" in win.title for win in minimized_windows)
           if not mission_planner_found:
                print("Mission Planner is not minimized. Launching it...")
                if launch_mission_planner() :
                   time.sleep(1)
                   active_window = gw.getActiveWindow()
                   if active_window and "Mission Planner" in active_window.title:
                        print("Mission Planner detected after launch! Maximizing...")
                        if not active_window.isMaximized:
                                pyautogui.hotkey("win", "up")
                                time.sleep(1)
                        media_player_rect = {
                        'left': active_window.left,
                        'top': active_window.top,
                        'width': active_window.width,
                        'height': active_window.height}
                        root.deiconify()  # Show the ROI Viewer again
                        root.lift()  # Bring ROI Viewer to the top
                        root.attributes("-topmost", True)  # Keep it above all windows
                        time.sleep(1)  
                        root.attributes("-topmost", False)  # Allow normal window interactions
                        return True 
                

        max_attempts = len(minimized_windows) if minimized_windows else 3  # Dynamically set attempts
        step = 1
        attempts = 0

        while attempts < max_attempts:
            for _ in range(step):
                pyautogui.press("right")
                time.sleep(0.5)

            pyautogui.press("enter")
            time.sleep(0.5)

            active_window = gw.getActiveWindow()
            if active_window:
                title = active_window.title.strip()

                if "Mission Planner" in title:
                    print("Mission planner found! Maximizing...")
                    if not active_window.isMaximized:
                        pyautogui.hotkey("win", "up")
                        time.sleep(1)
                    # Refresh window info after maximizing
                    active_window = gw.getActiveWindow()
                    media_player_rect
                    media_player_rect = {
                        'left': active_window.left,
                        'top': active_window.top,
                        'width': active_window.width,
                        'height': active_window.height
                    }
                    # Bring ROI Viewer to the front
                    
                    root.deiconify()  # Show the ROI Viewer again
                    root.lift()  # Bring ROI Viewer to the top
                    root.attributes("-topmost", True)  # Keep it above all windows
                    time.sleep(1)  
                    root.attributes("-topmost", False)  # Allow normal window interactions
                    return True

            pyautogui.hotkey("win", "tab")
            step += 1
            attempts += 1

        print("Mission Planner not found!")
        if launch_mission_planner():
            time.sleep(1)
            active_window = gw.getActiveWindow()
            if active_window and "Mission Planner" in active_window.title:
                print("Mission Planner detected after launch! Maximizing...")
                if not active_window.isMaximized:
                        pyautogui.hotkey("win", "up")
                        time.sleep(1)
                media_player_rect = {
                'left': active_window.left,
                'top': active_window.top,
                'width': active_window.width,
                'height': active_window.height}
                root.deiconify()  # Show the ROI Viewer again
                root.lift()  # Bring ROI Viewer to the top
                root.attributes("-topmost", True)  # Keep it above all windows
                time.sleep(1)  
                root.attributes("-topmost", False)  # Allow normal window interactions
                return True
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False

def switch_to_mission_planner():
    """Switch to and maximize Mission planner."""
    global media_player_rect
    success = maximize_until_mission_planner()
    if success:
        show_rois_button.config(state=tk.NORMAL)
        switch_button.config(state=tk.DISABLED) 
    else:
        messagebox.showerror("Error", "Failed to find Mission Planner.")

def draw_rois_with_matplotlib(ax):
    """Draw ROIs on the matplotlib figure."""
    for i, region in enumerate(regions):
        color = 'green' if selected_roi != i else 'red'
        rect = Rectangle(
            (region['left'], region['top']),
            region['width'],
            region['height'],
            linewidth=2, edgecolor=color, facecolor='none'
        )
        ax.add_patch(rect)
        ax.text(region['left'], region['top'] - 5, region['name'], 
                color=color, fontsize=12, fontweight='bold')

def on_click(event):
    """Handle mouse clicks to select ROIs."""
    global selected_roi, dragging, drag_start
    x, y = int(event.xdata), int(event.ydata)
    if event.button == 1:
        for i, region in enumerate(regions):
            if (region['left'] <= x <= region['left'] + region['width'] and
                region['top'] <= y <= region['top'] + region['height']):
                selected_roi = i
                dragging = True
                drag_start = (x, y)
                break

def on_motion(event):
    """Handle mouse motion to drag ROIs."""
    global dragging, drag_start
    if dragging and selected_roi is not None and event.xdata and event.ydata:
        dx = int(event.xdata) - drag_start[0]
        dy = int(event.ydata) - drag_start[1]
        regions[selected_roi]['left'] += dx
        regions[selected_roi]['top'] += dy
        drag_start = (int(event.xdata), int(event.ydata))
        update_plot()

def on_release(event):
    """Stop dragging on mouse release."""
    global dragging
    dragging = False

def save_rois_to_file():
    """Convert ROIs to absolute coordinates and save to file."""
    global media_player_rect
    if media_player_rect is None:
        messagebox.showerror("Error", "Mission planner rect not available.")
        return

    with open('rois.txt', 'w') as file:
        for region in regions:
            abs_left = region['left'] + media_player_rect['left']
            abs_top = region['top'] + media_player_rect['top']
            file.write(f"{abs_top},{abs_left},{region['width']},{region['height']},{region['name']}\n")

def update_plot():
    """Refresh the matplotlib plot."""
    plt.cla()
    img_rgb = cv2.cvtColor(screen_snapshot, cv2.COLOR_BGR2RGB)
    plt.imshow(img_rgb)
    draw_rois_with_matplotlib(plt.gca())
    plt.draw()

def show_rois_with_matplotlib(relative_regions):
    """Display the ROI adjustment interface."""
    fig, ax = plt.subplots()
    img_rgb = cv2.cvtColor(screen_snapshot, cv2.COLOR_BGR2RGB)
    ax.imshow(img_rgb)
    draw_rois_with_matplotlib(ax)

    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('motion_notify_event', on_motion)
    fig.canvas.mpl_connect('button_release_event', on_release)

    plt.title("Adjust ROIs - Close window when done")
    plt.show()
    save_rois_to_file()

def on_show_rois_button_click():
    """Capture Mission planner window and enable ROI adjustment."""
    global media_player_rect, regions, screen_snapshot
    if media_player_rect is None:
        messagebox.showerror("Error", "Switch to Mission planner first.")
        return

    # Capture live Mission planner window
    with mss.mss() as sct:
        monitor = {
            'left': media_player_rect['left'],
            'top': media_player_rect['top'],
            'width': media_player_rect['width'],
            'height': media_player_rect['height']
        }
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        screen_snapshot = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    if screen_snapshot is not None:
        # Convert regions to relative coordinates
        relative_regions = copy.deepcopy(regions)
        for region in relative_regions:
            region['left'] -= media_player_rect['left']
            region['top'] -= media_player_rect['top']
        show_rois_with_matplotlib(relative_regions)
        start_logging_button.config(state=tk.NORMAL)
        stop_logging_button.config(state=tk.NORMAL)
    else:
        messagebox.showerror("Error", "Failed to capture window.")

def on_start_logging_button_click():
    """Start the logging process."""
    global capture_process
    if not os.path.exists('stop_logging.txt'):
        open('stop_logging.txt', 'w').close()
    capture_process = subprocess.Popen(['python', 'main.py'])

def on_stop_logging_button_click():
    """Stop the logging process."""
    if capture_process:
        with open('stop_logging.txt', 'w') as f:
            f.write('stop')
        capture_process.terminate()

# GUI Setup
root = tk.Tk()
root.title("ROI Viewer")

window_width = 300
window_height = 300
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = 1600
y = 600
root.geometry(f"{window_width}x{window_height}+{x}+{y}")
root.resizable(False, False)

style = ttk.Style()
style.configure("TButton", font=("Helvetica", 10), padding=8)

frame = ttk.Frame(root, padding="20")
frame.pack(fill=tk.BOTH, expand=True)

switch_button = ttk.Button(
    frame,
    text="Switch to Mission Planner",
    command=switch_to_mission_planner,
    style="TButton"
)
switch_button.pack(fill=tk.X, pady=5)

show_rois_button = ttk.Button(
    frame,
    text="Select ROI",
    command=on_show_rois_button_click,
    style="TButton",
    state=tk.DISABLED
)
show_rois_button.pack(fill=tk.X, pady=5)

start_logging_button = ttk.Button(
    frame,
    text="Start Logging",
    command=on_start_logging_button_click,
    style="TButton",
    state=tk.DISABLED
)
start_logging_button.pack(fill=tk.X, pady=5)

stop_logging_button = ttk.Button(
    frame,
    text="Stop Logging",
    command=on_stop_logging_button_click,
    style="TButton",
    state=tk.DISABLED
)
stop_logging_button.pack(fill=tk.X, pady=5)

stop_program_button = ttk.Button(
    frame,
    text="Stop Program",
    command=on_stop_program_button_click,
    style="TButton"
)
stop_program_button.pack(fill=tk.X, pady=5)


instructions_label = tk.Label(
    frame,
    text="Workflow:\n1. Switch to Media Player\n2. Select ROIs\n3. Start/Stop Logging",
    justify=tk.LEFT
)
instructions_label.pack(pady=10)

root.mainloop()
