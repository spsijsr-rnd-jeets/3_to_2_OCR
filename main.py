import mss
import cv2
import numpy as np
import easyocr
import csv
import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk

# Global variable to control logging state
is_logging = True

# Load the regions of interest (ROIs) from the file
def load_rois():
    """Load the regions of interest from a text file."""
    loaded_regions = []
    try:
        with open('rois.txt', 'r') as file:
            for line in file:
                # The last value in the line is the ROI name (e.g., 'roi1')
                top, left, width, height, name = line.strip().split(',')
                loaded_regions.append({
                    'top': int(top),
                    'left': int(left),
                    'width': int(width),
                    'height': int(height),
                    'name': name  # Keep the name as a string
                })
    except FileNotFoundError:
        print("rois.txt file not found. Using default ROI positions.")
        return   # If no file, fall back to default regions

    return loaded_regions

# Capture the screen based on a region (ROI)
def capture_roi(region):
    with mss.mss() as sct:
        monitor = {"top": region['top'], "left": region['left'], "width": region['width'], "height": region['height']}
        screen = sct.grab(monitor)
        img = np.array(screen)
        return img

# Preprocess the image for ROI1 and ROIs 4-9 (digits)
def preprocess_digits(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary_img = cv2.threshold(gray_img, 128, 255, cv2.THRESH_BINARY)
    return binary_img

# Preprocess the image for ROI2 (red text) and ROI3 (red and white text)
def preprocess_red_and_white(img, roi_index):
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define lower and upper bounds for red color in HSV space
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])

    # Create masks for red color
    mask1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
    red_mask = mask1 | mask2

    # If processing ROI3, add white color mask
    if roi_index == 3:
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv_img, lower_white, upper_white)
        combined_mask = red_mask | white_mask
    else:
        combined_mask = red_mask

    # Bitwise-AND mask with the original image to get the red/white regions
    filtered_img = cv2.bitwise_and(img, img, mask=combined_mask)

    # Convert the filtered image to grayscale for further processing
    gray_img = cv2.cvtColor(filtered_img, cv2.COLOR_BGR2GRAY)
    _, binary_img = cv2.threshold(gray_img, 50, 255, cv2.THRESH_BINARY)
    return binary_img

# Extract text from an image using EasyOCR
def extract_text_from_image(img, reader):
    result = reader.readtext(img)
    return result

# Save data to CSV (buffered)
def save_to_csv(data, csv_filename='readings.csv'):
    file_exists = os.path.isfile(csv_filename)
    with open(csv_filename, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            # Write header only if the file does not exist
            writer.writerow(['Timestamp'] + [f"ROI {i+1} Text" for i in range(len(data))])
        writer.writerow([datetime.now()] + data)

# Process a single region (capture ROI, preprocess, OCR)
def process_roi(region, reader, roi_index):
    img = capture_roi(region)  # Capture the screen from the region
    
    # Preprocess based on ROI index
    if roi_index in [1, 4, 5, 6, 7, 8, 9]:  # Digits
        preprocessed_img = preprocess_digits(img)
    elif roi_index == 2:  # Red text
        preprocessed_img = preprocess_red_and_white(img, roi_index)
    elif roi_index == 3:  # Red and white text
        preprocessed_img = preprocess_red_and_white(img, roi_index)
    elif roi_index == 10:  # Orange text
        preprocessed_img = preprocess_red_and_white(img, roi_index)
    else:
        preprocessed_img = img  # Default case, no processing

    text_data = extract_text_from_image(preprocessed_img, reader)  # Extract text from the image
    text_result = ' '.join([text[1] for text in text_data]) if text_data else ''
    
    # Return the text result and whether the ROI1 contains digits (only for ROI1)
    if roi_index == 1:
        contains_digits = any(char.isdigit() for char in text_result)
        with open("roi1_status.txt", "w") as f:
             f.write("DETECTED" if contains_digits else "NOT DETECTED")
        return text_result, contains_digits
    return text_result, True  # Return True for other ROIs by default

# Modify the main function to check ROI1 before logging
def main():
    global is_logging
    reader = easyocr.Reader(['en'], gpu=False)  # Initialize EasyOCR reader for English language (CPU mode)
    regions = load_rois()  # Load the regions of interest from file

    # Create a thread pool for concurrent processing
    with ThreadPoolExecutor() as executor:
        try:
            while True:
                # Check for stop logging flag
                if not is_logging:
                    # If not logging, wait until resumed
                    time.sleep(0.5)
                    continue

                
                # Process the other ROIs in parallel
                future_readings = [executor.submit(process_roi, region, reader, idx + 1) 
                                        for idx, region in enumerate(regions)]
                        
                # Collect the results from all threads
                readings = [future.result()[0] for future in future_readings]
                        
                # Save results to CSV
                save_to_csv(readings)

                
                # Delay for 400ms
                time.sleep(0.4)

        except KeyboardInterrupt:
            print("Terminating due to keyboard interrupt.")

# Control logging state from the Tkinter UI
def toggle_logging():
    global is_logging
    is_logging = not is_logging
    button_text = "Resume Logging" if not is_logging else "Pause Logging"
    btn_pause_resume.config(text=button_text)

# Create a simple Tkinter UI
def create_ui():
    global btn_pause_resume

    root = tk.Tk()
    root.title("OCR Logger")
    
    # Position the window at the bottom right corner with padding
    window_width = 300
    window_height = 100
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = screen_width - window_width - 20  # 20 pixels from the right
    y = screen_height - window_height - 20  # 20 pixels from the bottom
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    btn_pause_resume = tk.Button(root, text="Pause Logging", command=toggle_logging)
    btn_pause_resume.pack(pady=20)

    root.protocol("WM_DELETE_WINDOW", root.quit)  # Handle window close
    root.mainloop()

if __name__ == "__main__":
    # Start the Tkinter UI in a separate thread
    import threading
    threading.Thread(target=create_ui, daemon=True).start()

    # Start the main function
    main()
