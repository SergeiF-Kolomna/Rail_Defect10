import cv2
import numpy as np
import PySimpleGUI as sg        # интерфейс
import sys
import Find_threshold_brown as ft     # самописный
import os       #для извлечения имени файла из пути

# -*- coding: utf-8 -*-

point1 = None
point2 = None
frame_start = None
frame_end = None
#frame_resizing = False
#image = None
image_mini = None
#threshold_value = 207
dark_spots = []
etalon_line = 100
#scale_percent = 30 # percent of original size. To compress the image
names = []
dark_spots_dict = {}
sum=0
#first_enter=False #  bool variable for once fill the list
ipass = 0

def calculate_distance(p1, p2):
    return (p2[0] - p1[0]) 
   
try:
    threshold_value, image_mini, dark_spots, frame_start, frame_end, point1, point2, file_path = ft.main()
except:
    pass
    
#cv2.imshow("Image", image_mini)
key = cv2.waitKey(0)

#dark_spots = on_key(key)
if dark_spots:

    #формируем словарь   ///этот кусок кода для отображения окошка со списком найденных дефектов
    numbers = list(range(0, len(dark_spots)))
    dark_spots_dict =dict(zip(numbers, dark_spots))

    for i in range(len(dark_spots_dict)):
        names.append(str(i))
    layout_lst = [[sg.Text('Rail',size=(20, 1), font='Lucida',justification='left')],
                    [sg.Listbox(names, select_mode='single', key='list1', size=(30, 6))],
                    [sg.Button('Remove', font=('Times New Roman', 12)),sg.Button('Cancel', font=('Times New Roman',12)), 
                        sg.Button('Back', font=('Times New Roman',12)), sg.Button('Next', font=('Times New Roman',12)), sg.Button('Calculate', font=('Times New Roman',12))]]
    window_list=sg.Window('Defects', layout_lst)
    #first_enter =True

    ttemp_image = image_mini.copy()
    for dark_spot in dark_spots:
        (x, y, w, h, dimensions) = dark_spot
        cv2.rectangle(ttemp_image, (x + frame_start[0], y + frame_start[1]), (x + frame_start[0] + w, y + frame_start[1] + h), (0, 255, 0), 2)
    file_name= os.path.basename(file_path)
    while True:
        if key == ord("q"):
            break
        sum=0
        e,v=window_list.read()
        if  v['list1'] == [] or v['list1'] == ['0']:
            v['list1']=str(ipass)
        print(e, v, ' ipass > ', ipass)

        temp_list=list(dark_spots_dict.keys())
        v['list1']=str(temp_list[int(ipass)])

        if e == 'Remove':
            names.remove(v['list1'])
            dark_spots_dict.pop(int(v['list1']))
            window_list['list1'].update(names)
            temp_list=list(dark_spots_dict.keys())
            temp2_image = image_mini.copy()
            for new_spot_list in dark_spots_dict:
                (x, y, w, h, dimensions) = dark_spots_dict[new_spot_list]
                cv2.rectangle(temp2_image, (x + frame_start[0], y + frame_start[1]), (x + frame_start[0] + w, y + frame_start[1] + h), (255, 175, 0), 2)
            ipass-=1
        elif e == 'Cancel':
            window_list.close()
            break
        elif e == 'Next':
            if ipass<len(dark_spots_dict)-1:
                ipass+=1
            else:
                ipass=0
            temp_list=list(dark_spots_dict.keys())
            v['list1']=str(temp_list[ipass])
        elif e == 'Back':
            if ipass>1:
                ipass-=1
            else:
                ipass=len(dark_spots_dict)-1
            temp_list=list(dark_spots_dict.keys())
            v['list1']=str(temp_list[ipass])
        elif e == 'Calculate':
            for i in dark_spots_dict:
                sum += dark_spots_dict[i][4]
            try:
                cv2.putText(temp2_image, f"Summary Square: {sum:.5f} cm^2", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            except:
                temp2_image = image_mini.copy()
                for new_spot_list in dark_spots_dict:
                    (x, y, w, h, dimensions) = dark_spots_dict[new_spot_list]
                    cv2.rectangle(temp2_image, (x + frame_start[0], y + frame_start[1]), (x + frame_start[0] + w, y + frame_start[1] + h), (255, 175, 0), 2)
                cv2.putText(temp2_image, f"Summary Square: {sum:.5f} cm^2", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            my_txt_file_name = file_name.replace('.jpg', '.txt')
            my_txt_file = open('E:/AAA/Defect19/' + my_txt_file_name, "w+")
            my_txt_file.write('Имя файла ' + '\t' + ' Обнаружено дефектов ' + '\t' + ' Общая площадь дефектов,кв.см. ' + '\t' + ' Средняя площадь дефекта,кв.см. ' + '\n')
            my_txt_file.write(my_txt_file_name + '\t' + str(len(dark_spots_dict)) + '\t' + str("{:.2f}".format(sum)) + "\t" + str("{:.2f}".format(sum/len(dark_spots_dict))))
            my_txt_file.close()

        #  /// окончание куска кода для  отображения окошка со списком найденных дефектов
        temp_list=list(dark_spots_dict.keys())
        v['list1']=str(temp_list[ipass])
        (x, y, w, h, dimensions) = dark_spots_dict[int(v['list1'])]

        temp_image = ttemp_image.copy()
        cv2.rectangle(temp_image, (x + frame_start[0], y + frame_start[1]), (x + frame_start[0] + w, y + frame_start[1] + h), (0, 0, 255), 2)
        
        # Add dimensions text to the dark spot
        width_cm = w / (calculate_distance(point1, point2)/etalon_line)
        height_cm = h / (calculate_distance(point1, point2)/etalon_line)
        cv2.putText(temp_image, f"Square: {dimensions:.3f} cm^2", (x + frame_start[0], y + frame_start[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(temp_image, f"Width: {width_cm:.3f} cm", (x + frame_start[0], y + frame_start[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(temp_image, f"Height: {height_cm:.3f} cm", (x + frame_start[0], y + frame_start[1] + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("Image", temp_image)
        try:
            cv2.imshow("temp2_image", temp2_image)
        except: pass

cv2.destroyAllWindows()
