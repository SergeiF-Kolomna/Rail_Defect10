import cv2
import numpy as np
import PySimpleGUI as sg

point1 = None
point2 = None
frame_start = None
frame_end = None
frame_resizing = False
image = None
threshold_value = 207
dark_spots = []
etalon_line = 100
scale_percent = 30

def calculate_distance(p1, p2):
    return (p2[0] - p1[0])

def calculate_area(distance, pixel_per_cm):
    return ((etalon_line**2) * distance / (pixel_per_cm*etalon_line)** 2)

def calculate_dimensions(cropped_image, pixel_per_cm):
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_TOZERO_INV)

    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    dark_spots_in_frame = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 0:
            dimensions = calculate_area(area, pixel_per_cm)
            if dimensions > 0.1 and dimensions < 5.1  :  # Check if area is more than 0.1 sq.cm. and less then 5.1
                (x, y, w, h) = cv2.boundingRect(contour)

                # Draw rectangle around the dark spot relative to frame's coordinates
                dark_spots_in_frame.append((x, y, w, h, dimensions))

    return dark_spots_in_frame

def mouse_callback(event, x, y, flags, param):
    global point1, point2, frame_start, frame_end, frame_resizing, image_mini

    if event == cv2.EVENT_LBUTTONDOWN:
        if frame_start is None:
            frame_start = (x, y)
        elif frame_end is None:
            frame_end = (x, y)
            frame_resizing = True

    elif event == cv2.EVENT_MOUSEMOVE:
        if frame_resizing:
            frame_end = (x, y)
            temp_image = image_mini.copy()
            cv2.rectangle(temp_image, frame_start, frame_end, (255, 0, 0), 2)
            cv2.imshow("Image", temp_image)

    elif event == cv2.EVENT_LBUTTONUP:
        frame_resizing = False
        temp_image = image_mini.copy()
        cv2.rectangle(temp_image, frame_start, frame_end, (255, 0, 0), 2)
        cv2.imshow("Image", temp_image)

        # Set point1 and point2 when frame selection is complete
        if frame_start and frame_end:
            point1 = frame_start
            point2 = frame_end

def on_key(event):
    global point1, point2, image_mini, frame_start, frame_end, dark_spots

    if event == ord('a') and frame_start and frame_end:
        frame_start = (min(frame_start[0], frame_end[0]), min(frame_start[1], frame_end[1]))
        frame_end = (max(frame_start[0], frame_end[0]), max(frame_start[1], frame_end[1]))

        if frame_start[0] == frame_end[0] or frame_start[1] == frame_end[1]:
            print("Invalid frame size. Please try again.")
            return

        cropped_image = image_mini[frame_start[1]:frame_end[1], frame_start[0]:frame_end[0]]

        pixel_per_cm = calculate_distance(point1, point2) / etalon_line
        dark_spots = calculate_dimensions(cropped_image, pixel_per_cm)

        cropped_image_with_dimensions = cropped_image.copy()
        for dark_spot in dark_spots:
            (x, y, w, h, dimensions) = dark_spot
            cv2.rectangle(cropped_image_with_dimensions, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Cropped Image", cropped_image_with_dimensions)

def on_trackbar(val):
    global threshold_value, image_mini, dark_spots

    threshold_value = val

    if frame_start and frame_end:
        point1 = frame_start
        point2 = frame_end

        pixel_per_cm = calculate_distance(point1, point2) / etalon_line
        cropped_image = image_mini[frame_start[1]:frame_end[1], frame_start[0]:frame_end[0]]
        dark_spots = calculate_dimensions(cropped_image, pixel_per_cm)

        temp_image = image_mini.copy()
        for dark_spot in dark_spots:
            (x, y, w, h, dimensions) = dark_spot
            cv2.rectangle(temp_image, (x + frame_start[0], y + frame_start[1]), (x + frame_start[0] + w, y + frame_start[1] + h), (0, 255, 0), 2)

        cv2.imshow("Image", temp_image)

def main():
    global image, image_mini, dark_spots
    #Open file window
    layout = [
                [sg.Text('File'), sg.InputText(), sg.FileBrowse()],
                [sg.Submit(), sg.Cancel()]
             ]
    window = sg.Window('Open file to find defects', layout)

    event, values = window.read()

    if event == 'Submit':
        image_path = values[0] 

        image = cv2.imread(image_path)
        
        #compress image
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        image_mini = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        cv2.namedWindow("Image")
        cv2.setMouseCallback("Image", mouse_callback)
        cv2.createTrackbar("Threshold", "Image", threshold_value, 255, on_trackbar)

        #for dark_spot in dark_spots:
        #    (x, y, w, h, dimensions) = dark_spot
        #    cv2.rectangle(image_mini, (x, y), (x + w, y + h), (0, 255, 0), 2)

        window.close()
    
        # I should put this variables to property of class
        first_enter=False #  bool variable for once fill the list
        ipass = 0       # variable for pass in listBox

        #-----------------------------------------
        #image_path = "image_test2.jpg"
        #image = cv2.imread(image_path)

        #cv2.namedWindow("Image")
        #cv2.setMouseCallback("Image", mouse_callback)

        #cv2.createTrackbar("Threshold", "Image", threshold_value, 255, on_trackbar)

        while True:
            cv2.imshow("Image", image_mini)

            key = cv2.waitKey(0)

            if key == ord("q"):
                break

            if key == ord("a") and frame_start and frame_end:
                on_key(key)

        return threshold_value, image_mini, dark_spots, frame_start, frame_end, point1, point2, values[0]
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
cv2.destroyAllWindows()


