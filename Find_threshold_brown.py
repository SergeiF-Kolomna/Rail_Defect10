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
brown_spots = []
brown_spot_index = 0


def calculate_distance(p1, p2):
    return (p2[0] - p1[0])

def calculate_area(distance, pixel_per_cm):
    return ((etalon_line**2) * distance / (pixel_per_cm*etalon_line)** 2)

def calculate_dimensions(cropped_image, pixel_per_cm):
    global LH, LS, LV, UH, US, UV
    
    # Define a range for brown color in BGR format (you may need to adjust these values)
    lower_brown = np.array([LH, LS, LV], dtype=np.uint8)
    upper_brown = np.array([UH, US, UV], dtype=np.uint8)

    # Convert the cropped image to the HSV color space
    hsv_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2HSV)

    # Create a mask for the brown color within the defined range
    brown_mask = cv2.inRange(hsv_image, lower_brown, upper_brown)

    # Find contours of brown spots
    contours, _ = cv2.findContours(brown_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    dark_spots_in_frame = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 0:
            dimensions = calculate_area(area, pixel_per_cm)
            if dimensions > 0.05 and dimensions < 5.1  :  # Check if area is more than 0.1 sq.cm. and less then 5.1

                (x, y, w, h) = cv2.boundingRect(contour)

                # Draw rectangle around the brown spot relative to frame's coordinates
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
    global threshold_value, image_mini, dark_spots, LH, LS, LV, UH, US, UV

    threshold_value = val
    LH = cv2.getTrackbarPos("LH", "Image")
    LS = cv2.getTrackbarPos("LS", "Image")
    LV = cv2.getTrackbarPos("LV", "Image")
    UH = cv2.getTrackbarPos("UH", "Image")
    US = cv2.getTrackbarPos("US", "Image")
    UV = cv2.getTrackbarPos("UV", "Image")

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

def white_balance(img):
    result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    return result

def nothing(x):
    pass

def main():
    global image, image_mini, dark_spots
    #Open file window
    rb=[]
    rb.append(sg.Radio("THRESH_BINARY", "my_group", key='TB', default=True))
    rb.append(sg.Radio("THRESH_BINARY_INV", "my_group", key='TBI'))
    layout = [
                [sg.Text('File'), sg.InputText(), sg.FileBrowse()],
                [sg.Submit(), sg.Cancel()],
                [rb]
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
        image_mini = white_balance(image_mini)
        cv2.namedWindow("Image")
        cv2.setMouseCallback("Image", mouse_callback)
        cv2.createTrackbar("Threshold", "Image", threshold_value, 255, on_trackbar)
        cv2.createTrackbar("LH", "Image", 0, 255, on_trackbar)
        cv2.createTrackbar("LS", "Image", 0, 255, on_trackbar)
        cv2.createTrackbar("LV", "Image", 0, 255, on_trackbar)
        cv2.createTrackbar("UH", "Image", 0, 255, on_trackbar)
        cv2.createTrackbar("US", "Image", 0, 255, on_trackbar)
        cv2.createTrackbar("UV", "Image", 0, 255, on_trackbar)
        # Set default positions
        cv2.setTrackbarPos('LH', 'Image', 0)
        cv2.setTrackbarPos('LS', 'Image', 0)
        cv2.setTrackbarPos('LV', 'Image', 100)
        cv2.setTrackbarPos('UH', 'Image', 55)
        cv2.setTrackbarPos('US', 'Image', 160)
        cv2.setTrackbarPos('UV', 'Image', 209)
         
        window.close()
    
        # I should put this variables to property of class
        first_enter=False #  bool variable for once fill the list
        ipass = 0       # variable for pass in listBox

        while True:
            cv2.imshow("Image", image_mini)

            key = cv2.waitKey(0)

            if key == ord("q"):
                break

            if key == ord("a") and frame_start and frame_end:
                on_key(key)

        return threshold_value, image_mini, dark_spots, frame_start, frame_end, point1, point2, values[0], LH, LS, LV, UH, US, UV
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
cv2.destroyAllWindows()



