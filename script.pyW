import cv2
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import shutil
import math
from skimage.metrics import structural_similarity as ssim

project_title="FramesExtactor_GUI"

current_directory  = os.path.dirname(os.path.abspath(__file__))
input_directory  = os.path.join(current_directory, "INPUT")
output_directory = os.path.join(current_directory, "OUTPUT")
masks_folder_path = os.path.join(current_directory, "0_MASKS")

format_options = ["png", "jpg"]
extract_mode_options = ["Frames", "Seconds"]

def measure_similarity(input_image, pictures_array, cropScore = -1):
    # Load the input picture
    gray_input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    # Calculate the similarity between the input picture and each picture in the array
    similarity_scores = []
    doCrop = False
    if(len(pictures_array)==0):
        print("empty Compar Array")
        return False
    cnt = 0
    for compare_image in pictures_array:
        gray_compare_image = cv2.cvtColor(compare_image, cv2.COLOR_BGR2GRAY)

        # Compute the structural similarity index (SSIM)
        similarity = ssim(gray_input_image, gray_compare_image)

        # Add the similarity score to the list
        similarity_scores.append(("input_picture", "F-"+str(cnt), similarity))
        cnt+=1

    # Sort the similarity scores in descending order
    similarity_scores.sort(key=lambda x: x[2], reverse=True)

    # Print the similarity scores
    for (input_picture, compr_picture, similarity) in similarity_scores:
        print(f"Similarity between {input_picture} and {compr_picture}: {similarity}")
        if (similarity > cropScore)and(cropScore>0) :
           doCrop = True 

    return doCrop


def process_images(inputDir, outputDir,interveal , format_option = "png",extractBySeconds=False, pruneScore =-1 , progressGui=None,rootGui=None, text_Gui_elem=None):


    # Get a list of video files in the input directory
    video_files = [f for f in os.listdir(inputDir) if os.path.isfile(os.path.join(inputDir, f))]

    vid_counter = 0
    for video_file in video_files:
        framesArray = []
        video_path = os.path.join(inputDir, video_file)
        
        # Create a subdirectory in the output directory for each video file
        video_output_directory = os.path.join(outputDir, os.path.splitext(video_file)[0])
        os.makedirs(video_output_directory, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        vid_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        frame_counter = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if extractBySeconds : 
                testCond = frame_counter % (interveal*frame_rate) == 0
            else :
                testCond = frame_counter % interveal == 0

            if testCond:
                frame_path = os.path.join(video_output_directory, f'frame_{frame_counter}.'+format_option)
                pruneFrame = False
                if(pruneScore>0):
                    pruneFrame = measure_similarity(frame,framesArray,pruneScore) 
                    print("frame Pruned due to a similarity flag!")
                
                if not pruneFrame :
                    cv2.imwrite(frame_path, frame)
                    framesArray.append(frame)
            
            frame_counter += 1
            progressGui['value'] =  int((frame_counter / math.floor(vid_frame_count)) * 100)
            rootGui.update()  
        
        cap.release()
        vid_counter +=1
        text_Gui_elem.config(text="Status:  "+str(vid_counter) +" / "+str(len(video_files))+"  VIDs PROCESSED")
        rootGui.update()
        print(f"Frames extracted from {video_file} and saved in {video_output_directory}")

    text_Gui_elem.config(text="Status:  "+"ALL VIDEOS PROCESSED ✅")
    rootGui.update()
    print("Frame extraction completed.")


#---------------------[Events]--------------

def toggleDisable (guiElem, state):
    if(state==True):
        guiElem.config(state="normal")
    else:
        guiElem.config(state="disabled")    


def button_click(text_Gui_elem,interval,mode, format ,empty_output,pruneSimilar,pruneScore,progress, btn ,rootGui):
    
    if os.path.exists(output_directory)and empty_output:
        try:
            shutil.rmtree(output_directory)
        except OSError as e:
            print(f"An error occurred while clearting the folder: {str(e)}")
            text_Gui_elem.config(text="Error: make sure the Output folder is closed")
            rootGui.update()
            return
    os.makedirs(output_directory, exist_ok=True)

    try:
        intrVal = int(interval)
    except ValueError:
        text_Gui_elem.config(text="Error: invalid interval value format")
        rootGui.update()
        return
    
    if(pruneSimilar):
        try:
            prScore =  float(pruneScore)
        except ValueError:
            text_Gui_elem.config(text="Error: similarity score needs to be between 0 and 1")
            rootGui.update()
            return
    else:
        prScore = -1


    text_Gui_elem.config(text="Status: PROCESSING...")
    btn.config(state="disabled")
    secondsMode = (mode == extract_mode_options[1])


    process_images(input_directory,output_directory,intrVal ,format, secondsMode , prScore, progress,rootGui,text_Gui_elem)
    
    btn.config(state="normal")

 

def path_update(text_Gui_elem, isInput=True):
    global input_directory
    global output_directory
    file_path = filedialog.askdirectory()
    if(file_path):
        if(isInput==True):
            input_directory = file_path
            text_Gui_elem.config(text= input_directory  )
            print("changed input Path to:    ",  file_path)
        else:
            output_directory = file_path
            text_Gui_elem.config(text= output_directory )
            print("changed output Path to:   ",  file_path)


#---------------------|GUI|-------------------
def buildGUI():
 


    window            = tk.Tk()
    window.title(project_title) 
    selectedFromat = tk.StringVar()
    framesInterval = tk.StringVar(value="20")
    selectedMode   = tk.StringVar()
    keepSubFolders    = tk.BooleanVar(value=True)
    similarityCheck = tk.BooleanVar(value=False)
    similarityScore = tk.StringVar(value="0.67")

 
    frame_general     = tk.LabelFrame(window, text="Path Options")

    frame_general.pack(fill=tk.BOTH, expand=True)
    frame_general.grid_rowconfigure   (0, weight=1)
    frame_general.grid_columnconfigure(0, weight=1)

    frame_from     = tk.LabelFrame(window, text="Frames Options")
    frame_from.pack(fill=tk.BOTH, expand=True)
    frame_from.grid_rowconfigure   (0, weight=1)
    frame_from.grid_columnconfigure(0, weight=1)


    frame_extra     = tk.LabelFrame(window, text="Extra Options")
    frame_extra.pack(fill=tk.BOTH, expand=True)
    frame_extra.grid_rowconfigure   (0, weight=1)
    frame_extra.grid_columnconfigure(0, weight=1)

    statusInfo     = tk.Label(window, text="Status: ON STAND BY")
    inText         = tk.Label(frame_general, text="Process Videos from: ",anchor='nw')
    inPathInfo     = tk.Label(frame_general, text= input_directory     ,anchor='nw')
    outText        = tk.Label(frame_general, text="Output Result in: "   ,anchor='nw')
    outPathInfo    = tk.Label(frame_general, text= output_directory    ,anchor='nw')
    out_mod_button = tk.Button(frame_general, text="Change Folder", command= lambda:path_update(outPathInfo) )
    in_mod_button  = tk.Button(frame_general, text="Change Folder", command= lambda:path_update(inPathInfo )  )
    keep_subFolders_check = tk.Checkbutton(frame_general, text="pre-clean output directory", variable=keepSubFolders)



    inInterval_label = tk.Label(frame_from, text="Extract Every: ")
    inInterval_label.grid  (row=0, column=0)
    inInterval     = tk.Entry(frame_from,textvariable=framesInterval )
    inInterval.grid        (row=0, column=1)
    inExtrMode     = ttk.Combobox(frame_from, textvariable=selectedMode, values=extract_mode_options)
    inExtrMode.set(extract_mode_options[0])
    inExtrMode.grid        (row=0, column=2)
    outFormat_label = tk.Label(frame_from, text="as: ")
    outFormat_label.grid        (row=0, column=3)
    outFormat      = ttk.Combobox(frame_from, textvariable=selectedFromat, values=format_options)
    outFormat.set(format_options[0])
    outFormat.grid        (row=0, column=4)

    scoreLimit_label        = tk.Label(frame_extra, text="Any Similarity Score Over: ")
    scoreLimit              = tk.Entry(frame_extra,textvariable=similarityScore,state='disabled')
    useSimil                = tk.Checkbutton(frame_extra, text="Prune By Similarity", variable=similarityCheck,command=lambda:toggleDisable(scoreLimit,similarityCheck.get()))

    useSimil.grid           (row=0, column=0)
    scoreLimit_label.grid   (row=0, column=1)
    scoreLimit.grid         (row=0, column=2)

    inText.grid        (row=0, column=0)
    inPathInfo.grid    (row=0, column=1)
    in_mod_button.grid (row=0, column=2)
    outText.grid       (row=1, column=0)
    outPathInfo.grid   (row=1, column=1)
    out_mod_button.grid(row=1, column=2)

    keep_subFolders_check.grid(row=2, column=0)

    progress = ttk.Progressbar(window, orient='horizontal', length=200, mode='determinate'  )
    


    # Runs the main function
    go_button     = tk.Button(window, text="Proccess Input", command= lambda:button_click(statusInfo,framesInterval.get(),selectedMode.get(),selectedFromat.get(),keepSubFolders.get(),similarityCheck.get(),similarityScore.get(),progress,go_button,window) )
 
    frame_general.pack()
    statusInfo.pack()
    progress.pack()
    go_button.pack()

    # Start the event loop
    window.mainloop()


buildGUI()