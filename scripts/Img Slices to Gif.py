
import os
import uuid 
import math
import modules.scripts as scripts
import gradio as gr
import numpy as np

from modules.processing import process_images, Processed, fix_seed
from modules.shared import opts, cmd_opts, state
from modules import extra_networks
from PIL import Image



global_Title = "Img Slices to Gif"
global_scriptEnabled = False
global_cuts_x = 2
global_cuts_y = 2




#----------------------------|SD Block|-------------------------------

def main(p,task_enabled ,task_x_slices ,task_y_slices ,task_frameDuration,task_enableFreezes,task_enablePingpong ,task_freezesDuration): 
  
    imgs = []
    all_prompts = []
    infotexts = []
    cNet=False

    print()
    print("Cutting into  :",task_x_slices*task_y_slices," frames")
    print()
    fix_seed(p)
  
    proc = process_images(p)


    if(len(proc.images)>1):
        imgs.append(slice_image(proc.images[0],task_x_slices ,task_y_slices))
        cNet=True
    else:
        #imgs.append(proc.images)
        imgs = slice_image(proc.images[0],task_x_slices ,task_y_slices)


    all_prompts.append(proc.all_prompts)
    infotexts.append(proc.infotexts)

    if(task_enableFreezes==True):
        print("task_enableFreezes==True   and task_freezesDuration= ",task_freezesDuration)
        imgs += [imgs[-1]]*task_freezesDuration
        imgs = ([imgs[0]]*task_freezesDuration) + imgs

    if(task_enablePingpong==True):
        imgs+=imgs[::-1]
 
    gif = [make_gif(imgs ,"" ,task_frameDuration )]

    if(cNet==False):
        imgs += gif

  
    return Processed(p, gif, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)




#------------------------|Main ulitity|-------------------------------
def slice_image(img, nx, ny):

    width, height = img.size
    slice_width = width // nx
    slice_height = height // ny

    # Slice the image into nx x ny sections
    slices = []
    for i in range(nx):
        for j in range(ny):
            slices.append(img.crop((j * slice_width, i * slice_height, (j + 1) * slice_width, (i + 1) * slice_height)))
            

    # Return the slices as a list of PIL Image objects
    return slices

def make_gif(frames, filename = "", frame_time=100, gif_loop=True):

    print()
    print("Adding :",len(frames),"frames")
    print()

    if filename=="":
      filename = "PromptAnimation_"+str(uuid.uuid4())

    outpath = "outputs/txt2img-images/txt2gif"
    if not os.path.exists(outpath):
        os.makedirs(outpath)


    first_frame, append_frames = frames[0], frames[1:]
    
    if(gif_loop==False):
        g_loop=1
    else:
        g_loop=0


    first_frame.save(f"{outpath}/{filename}.gif", format="GIF", append_images=append_frames,
               save_all=True, duration=frame_time, loop=g_loop)
               
    print()
    print(f"Gif #", len(frames),"F Created in: {outpath}/{filename}.gif")
    print()

    return first_frame

#------------------------|Gradio Events|------------------------------
def toggeleFreeze(inBool):
    return gr.update(visible = inBool) 

def toggeleWorkspace(inBool):
    global global_scriptEnabled
    global_scriptEnabled = inBool
    return gr.update(visible = global_scriptEnabled) 

def updateInfo(inSiderX, inSiderY):
    global global_cuts_x
    global global_cuts_y
    global_cuts_x = inSiderX
    global_cuts_y = inSiderY
    return gr.update(value  = "Resulted cropped images count :   " + str(global_cuts_y*global_cuts_x)) 

#-------------------------|Auto1111 Block|----------------------------
class Script(scripts.Script):
    is_txt2img = False

    # Function to set title
    def title(self):
        return global_Title

    def ui(self, is_img2img):
        with gr.Row():
            task_enabled =  gr.Checkbox(label="Enable",value = global_scriptEnabled)
        with gr.Column(visible = global_scriptEnabled) as ui_workspace:
            with gr.Row():
                task_x_slices      = gr.Slider(label="X slices"       , value = 2  ,minimum = 2, maximum =10  ,interactive = True ,step= 1    ,info="How many slices on the X axies" )
                task_y_slices      = gr.Slider(label="Y slices"       , value = 2  ,minimum = 2, maximum =10  ,interactive = True ,step= 1    ,info="How many slices on the Y axies" )
            with gr.Row():
                extra_Info    = gr.Markdown( value = "Resulted cropped images count :   4" )
            with gr.Accordion(open=False, label="Extra options"):
                with gr.Row():
                    task_frameDuration  = gr.Slider(label="Frame Duration ", value = 0.5,maximum = 5, minimum= 0.01,interactive = True ,step= 0.01 ,info ="The delay between frames in seconds" )
                    task_enablePingpong = gr.Checkbox(label="Pingpong loop",value = False,info ="Makes the GIF play back and forth")
                with gr.Row():
                    task_enableFreezes   = gr.Checkbox(label="Add Halts",value = False,info ="Adds a short halt the a start and end of the GIF")
                    task_freezesDuration = gr.Slider(label="Halt duration"       , value = 3  ,minimum = 2, maximum =15  ,interactive = True ,step= 1, visible =False )
            
        task_enabled.change        ( fn = toggeleWorkspace,inputs = task_enabled      , outputs=  ui_workspace) 
        task_enableFreezes.change  ( fn = toggeleFreeze   ,inputs = task_enableFreezes, outputs=  task_freezesDuration) 
        task_x_slices.change ( fn = updateInfo,inputs = [task_x_slices,task_y_slices] , outputs=  extra_Info)   
        task_y_slices.change ( fn = updateInfo,inputs = [task_x_slices,task_y_slices] , outputs=  extra_Info)   

        
        return [task_enabled ,task_x_slices ,task_y_slices ,task_frameDuration, task_enableFreezes ,task_enablePingpong ,task_freezesDuration]

    # Function to show the script
    def show(self, is_img2img):
        return True

    # Function to run the script
    def run(self, p,task_enabled ,task_x_slices ,task_y_slices ,task_frameDuration,task_enableFreezes ,task_enablePingpong ,task_freezesDuration):
        # Make a process_images Object
        if(task_enabled):        
            return main(p,task_enabled ,task_x_slices ,task_y_slices ,task_frameDuration,task_enableFreezes,task_enablePingpong ,task_freezesDuration)

#---------------------------------------------------------------------