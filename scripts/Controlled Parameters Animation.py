
import os
import uuid 
import time
import math
import modules.scripts as scripts
import gradio as gr
import numpy as np

from modules.processing import process_images, Processed, fix_seed
from modules.shared import opts, cmd_opts, state
from modules import extra_networks



global_Title = "Controlled Parameters Animation"

#------------------------|Gradio Block|-------------------------------
def notInt(value):
    return value!=int(value)



def fetchFromByLabel(src , label):
    res = [data for data in src if label==data.label]
    return res[0] if res else None

def verifyLayerValidity(Layer):
    msg = "" 
    paramTypeData = fetchFromByLabel(paramTypes, Layer.paramType)
    
    if(Layer.stepSize<=0): msg+= " | Step Size must be positive "
    if(Layer.startVal==Layer.endVal): msg+= " | The Start and End values must be diffrent "
    if(Layer.val=="" and paramTypeData.useScope==1 ): msg+= " | Missing Text value "
    
    if( paramTypeData.varType ==int):
        if(notInt(Layer.stepSize)): msg+= " | Recheck the value type for the step "
        else:     Layer.stepSize = int(Layer.stepSize)
        if(notInt(Layer.startVal)): msg+= " | Recheck the value type for the Start Value "
        else:     Layer.startVal = int(Layer.startVal)
        if(notInt(Layer.endVal))  : msg+= " | Recheck the value type for the End Value "
        else:     Layer.endVal = int(Layer.endVal)
    
    if(msg): return """
                    ### ⛔ Invalid Layer : """+ msg
    else   : return Layer
    
    
def do_nothing(p, x, xs):
    pass

def estimateOutput(inpSelectedList, inEndCnd,inPlyMd):
    

    global framesCountByLayers 
    global framesCount 
    global addedFrames
    
    
    framesCountByLayers  = []
    activeLayersData = [paramLr  for paramLr in layersList if paramLr.label in inpSelectedList]
    
    print(len(activeLayersData))
    
    for lr in activeLayersData:
        framesCountByLayers+=[math.floor(abs(lr.startVal-lr.endVal)/lr.stepSize)]
    
    if(inEndCnd=="All Frames"):framesCount = max(framesCountByLayers)
    if(inEndCnd=="Min Frames"):framesCount = min(framesCountByLayers)
    if(inPlyMd=="Pingpong")   :addedFrames = framesCount


def updateEstimation(inpSelectedList, inFrmLn,inEndCnd,inPlyMd):
    
    if(len(inpSelectedList)==0): return gr.update(value = "ERROR: add some Parameter Layers first.")
    
    markupStr = """
    ### Expected Output: 
    """

    estimateOutput(inpSelectedList, inEndCnd,inPlyMd)
    
    
    markupStr+= """
    🎬Total Frame Count[""" + str(framesCount+addedFrames) +"]:   "
    markupStr+= str(framesCount) +"Calculated   /   "
    markupStr+= str(addedFrames) +"Reused  "
    markupStr+="""
    🕙Duration["""+ str((framesCount+addedFrames)*inFrmLn)  +"s] "
    
    return gr.update(value = markupStr)
  
def updateLayerInfo(inSelectedLayers):
    return gr.update(value = "Total active layers count: "+str(len(inSelectedLayers))+" / "+str(len(layersList)))

def changeUiByParam (inp):
    
    defStepsByType = {None:1,str:0.1,int:1,float:0.5}
    
    for item in paramTypes:  
        if item.label == inp: 
            selectedParam = item
            break
     
    return (gr.update(maximum = selectedParam.maxVal ,minimum= selectedParam.minVal ,step= defStepsByType[selectedParam.varType] ,value = selectedParam.minVal),
            gr.update(maximum = selectedParam.maxVal ,minimum= selectedParam.minVal ,step= defStepsByType[selectedParam.varType] ,value = selectedParam.minVal+(defStepsByType[selectedParam.varType]*5)),
            gr.update(label = selectedParam.label+" Value",visible = selectedParam.hasAuxVal ),
            gr.update(value = defStepsByType[selectedParam.varType]))

def addParamLayer(inpParam, inpStep, inpStart, inpFinish, selectedList, inpAuxVal ):
  
    createdLayer = verifyLayerValidity(paramLayer("label=layerName" ,paramType=inpParam ,stepSize=inpStep ,startVal=inpStart ,endVal=inpFinish,val=inpAuxVal ))
    if isinstance(createdLayer, str):
        return gr.update(), gr.update(value = createdLayer)
    
    
    dupe = []
    paramData = [pr for pr in paramTypes if pr.label==inpParam][0]

    
    if(paramData.useScope==1):
        createdLayer.label = "📃 "+inpParam+"<"+inpAuxVal+">"
        dupe=[lr for lr in layersList if (lr.val == inpAuxVal and lr.paramType == paramData.label)]
    else:
        createdLayer.label = "💠 "+inpParam
        dupe=[lr for lr in layersList if lr.paramType == paramData.label]
    createdLayer.label +=  " ["+str(inpStart)+" / "+str(inpFinish)+"]  @"+str(inpStep)
    if(len(dupe)>0):
        layersList[layersList.index(dupe[0])]= createdLayer
        if(dupe[0].label in selectedList): selectedList[selectedList.index(dupe[0].label)] = createdLayer.label
        else:selectedList.append(createdLayer.label)
    else:
        layersList.append(createdLayer)
        selectedList.append(createdLayer.label)

    displyLabels = [paramLr.label  for paramLr in layersList]
    

        
    
    
    return (gr.update(choices= displyLabels, value = selectedList   ) ,
            gr.update(value = "Total active layers count: "+str(len(selectedList))+" / "+str(len(displyLabels))))


def rmParamLayer(inp):
    displyLabels = [paramLr.label  for paramLr in layersList]
    removedItems = np.setdiff1d(displyLabels, inp)
    if removedItems :
        for item in layersList:  
            if item.label == removedItems[0]: 
                layersList.pop(layersList.index(item))
        displyLabels = [paramLr.label  for paramLr in layersList]
        return (gr.update(choices= displyLabels , value = inp ),
               gr.update(value = "Total active layers count: "+str(len(inp))+" / "+str(len(displyLabels))))
    


def clearParamLayers(inp):
    displyLabels = [paramLr.label  for paramLr in layersList]
    removedItems = np.setdiff1d(displyLabels, inp)
    if removedItems :
        for item in layersList:  
            if item.label == removedItems[0]: 
                layersList.pop(layersList.index(item))
        displyLabels = [paramLr.label  for paramLr in layersList]
        return (gr.update(choices= displyLabels),
               gr.update(value = "Total active layers count: "+str(len(inp))+" / "+str(len(displyLabels)) ) )
        
    
 
class ParamType: # useScope (0|1|2) 0 for atribute , 1 for prompt
    def __init__(self, label,varType, fieldName, maxVal, minVal = 0, hasAuxVal = False, useScope = 0,locked = False):
        self.label     = label
        self.varType   = varType
        self.fieldName = fieldName
        self.maxVal    = maxVal
        self.minVal    = minVal
        self.hasAuxVal = hasAuxVal
        self.locked    = locked
        self.useScope  = useScope
        
class paramLayer:
    def __init__(self, label, paramType, stepSize, startVal, endVal,active = True,val = ""):
        self.label     = label
        self.paramType = paramType
        self.stepSize  = stepSize
        self.startVal  = startVal
        self.endVal    = endVal
        self.active    = active
        self.val       =  val
        self.dir       = 1 if startVal <= endVal else -1
 


paramTypes = [
    ParamType("LoRA"            ,str    ,"none"     ,5,0,True,1),
    ParamType("Prompt Tag"      ,str    ,"none"     ,10,0,True,1),
    ParamType("Sampler Steps"   ,int    ,"steps"    ,150,1),
    ParamType("Seed"            ,int    ,"seed"     ,9000000000),  
    ParamType("CFG Scale"       ,float  ,"cfg_scale",10,1),
    ParamType("Clip skip"       ,int    ,"CLIP_stop_at_last_layers" ,12,1)
]

gif_playmods = ["Normal","Loop","Pingpong","Reverse"]

layersList    = []

dfPr = 0

framesCountByLayers = []
framesCount = 1
addedFrames = 0
 
#---------------------------------------------------------------------

#----------------------------|SD Block|-------------------------------



def spliceTextPrompt (textPrompt, loraName, loraWeight, loraMode = True):

    index = textPrompt.find(loraName+":")
    if index == -1:
        if(loraMode):return textPrompt+",<lora:"+loraName+":"+str(loraWeight)+"> ,"
        else        :return textPrompt+","      +loraName+":"+str(loraWeight)+"  ,"
    
    end_index = textPrompt.find(">", index)  
    if end_index == -1:  end_index = len(loraName)+2
    new_textPrompt = textPrompt[:index+len(loraName)+1] + loraWeight + textPrompt[end_index:]
    return new_textPrompt



def handleAttributeIteration(interator,layersList,p):
    opts_data_cases = ["Clip skip"]
    logStr = "ATTR | "
    for layer in layersList:
        curVal =layer.startVal+(interator * layer.stepSize * layer.dir)
        curVal =  max(curVal, layer.endVal ) if layer.dir==-1 else min(curVal, layer.endVal )
        
        field = [param.fieldName for param in paramTypes if layer.paramType == param.label][0]
        
        if(layer.paramType in opts_data_cases): opts.data[field] = curVal
        else: setattr(p, field, curVal)
        
        logStr+=field+": "+str(curVal)+" | "
    print(logStr)


def preBakePrompts(user_prompt, task_layers):
  
  prompts = []
  clonePrompt = None  

  for i in range(framesCount+1):
        clonePrompt = user_prompt
        for layer in task_layers: 
            curVal =layer.startVal+(i * layer.stepSize * layer.dir)
            curVal =  max(curVal, layer.endVal ) if layer.dir==-1 else min(curVal, layer.endVal )
            if(layer.paramType == "LoRA")       : clonePrompt = spliceTextPrompt(clonePrompt,layer.val,str(curVal))
            if(layer.paramType == "Prompt Tag") : clonePrompt = spliceTextPrompt(clonePrompt,layer.val,str(curVal),False)
        prompts+=[clonePrompt] 
           
  return prompts

def make_gif(frames, filename = "", frame_time=100, gif_loop=None):

    print()
    print("Adding :",addedFrames,"frames")
    print()

    if filename=="":
      filename = "PromptAnimation_"+str(uuid.uuid4())

    outpath = "outputs/txt2img-images/txt2gif"
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    if(gif_loop==gif_playmods[2]):frames+=frames[::-1]
    if(gif_loop==gif_playmods[3]):frames =frames[::-1]

    first_frame, append_frames = frames[0], frames[1:]
    
    
    if(gif_loop==gif_playmods[0]):
        g_loop=1
    else:
        g_loop=0
    



    first_frame.save(f"{outpath}/{filename}.gif", format="GIF", append_images=append_frames,
               save_all=True, duration=frame_time, loop=g_loop)
               
    print()
    print(f"Gif #", framesCount+addedFrames,"F Created in: {outpath}/{filename}.gif")
    print()

    return first_frame

def main(p,task_layers, task_frameDuration, task_endCondition, task_playMode): 
  
  imgs = []
  all_prompts = []
  infotexts = []
  workingLayers = [layer for layer in layersList if layer.label in task_layers]
  promptLayers =  [layer for layer in workingLayers if layer.paramType in [param.label for param in paramTypes if param.useScope==1]]
  AttribLayers =  [layer for layer in workingLayers if layer.paramType in [param.label for param in paramTypes if param.useScope==0]]


  estimateOutput(task_layers, task_endCondition,task_playMode)



  print("Total ParamLayer Count : ",len(workingLayers), "Layers")
  print("Controlling Attriubes: ",len(AttribLayers), "Layers")
  print("Controlling Prompt   : ",len(promptLayers), "Layers")

  if(promptLayers):
    user_prompt = p.prompt.strip().rstrip(',')
    preBaked_prompts = preBakePrompts(user_prompt, promptLayers)

  print()
  print("Generating :",framesCount,"frames")
  print()
  fix_seed(p)
  state.job_count = framesCount
  cNet=False
  
  for i in range(framesCount):
    if state.interrupted:
      break
    
    if(AttribLayers):handleAttributeIteration(i,AttribLayers,p)
    if(promptLayers):p.prompt = preBaked_prompts[i]
    proc = process_images(p)

    if state.interrupted:
      break  
    
    #print(i+1," of ",framesCount)
    #print()

    if(len(proc.images)>1):
        imgs.append(proc.images[0])
        cNet=True
    else:
        #imgs.append(proc.images)
        imgs += proc.images
    all_prompts.append(proc.all_prompts)
    infotexts.append(proc.infotexts)
    #print();
 
  gif = [make_gif(imgs ,"" ,task_frameDuration ,  task_playMode )]

  if(cNet==False):
   imgs += gif

  
  return Processed(p, gif, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)

#---------------------------------------------------------------------

#-------------------------|Auto1111 Block|----------------------------
class Script(scripts.Script):
    is_txt2img = False

    # Function to set title
    def title(self):
        return global_Title

    def ui(self, is_img2img):
 
        with gr.Row():
            with gr.Column():
                layer_add    = gr.Button(value="✅ Add Parameter Layer")
                layer_clear  = gr.Button(value="❌ Clear Unused Layers")
            layer_param      = gr.Dropdown(choices=[paramTp.label  for paramTp in paramTypes], value =paramTypes[dfPr].label , label="Parameter Type", info="select a parameter to control",interactive = True)
            layer_auxValue   = gr.Textbox(label= paramTypes[dfPr].label+" Name", info="Input just the name",interactive = True, visible = paramTypes[dfPr].hasAuxVal)
            
        with gr.Row():
            layer_step   = gr.Number(label="Step size"   , value = 0.1,interactive = True, info="How much does the pramater's value move each frame")
            layer_start  = gr.Slider(label="Start value" , value = 0  ,interactive = True, info="The pramater's inital value",maximum = paramTypes[dfPr].maxVal, minimum= paramTypes[dfPr].minVal,step= abs(paramTypes[dfPr].maxVal-paramTypes[dfPr].minVal)/20)
            layer_finish = gr.Slider(label="Finish value", value = 1  ,interactive = True, info="The pramater's traget value", maximum = paramTypes[dfPr].maxVal, minimum= paramTypes[dfPr].minVal,step= abs(paramTypes[dfPr].maxVal-paramTypes[dfPr].minVal)/20)
        
        with gr.Row():
            extra_layersInfo    = gr.Markdown( value = "Total active layers count: 0 / "+str(len(layersList)) )        
        
        with gr.Row():

            task_layers        = gr.Dropdown(choices=[], label="Parameter Layers", info="View added layers and toggle them on or off  ",interactive = True, multiselect = True, max_choices = 4)
        with gr.Accordion(open=False, label="Extra options"):
            with gr.Row():
                task_frameDuration = gr.Slider(label="Frame Duration ", value = 0.5,interactive = True, maximum = 5, minimum= 0.01, step= 0.01,info ="The delay between frames in seconds" )
                task_endCondition  = gr.Dropdown(label="End Condition ", choices=["All Frames","Min Frames"] , value ="All Frames" , info="Choose the number of frames to process by layers end value",interactive = True)
                task_playMode      = gr.Radio(label ="Animation play mode ",choices = gif_playmods ,value = gif_playmods[1],interactive = True)
            with gr.Row():
                extra_estimBtn    = gr.Button(value="Estimate Output")
                extra_estimText    = gr.Markdown( )
            
        
        
            
            
        layer_param.change(fn=changeUiByParam,inputs = layer_param ,outputs=[layer_start,layer_finish,layer_auxValue,layer_step])
        #task_layers.change(rmParamLayer,task_layers,task_layers)
        layer_clear.click( fn = rmParamLayer,outputs =  [task_layers,extra_layersInfo]  ,inputs = task_layers)
        task_layers.change(fn = updateLayerInfo, inputs = task_layers , outputs = extra_layersInfo)
        layer_add.click( fn = addParamLayer, outputs =  [task_layers,extra_layersInfo]  ,inputs = [layer_param,layer_step,layer_start,layer_finish,task_layers,layer_auxValue] )
        extra_estimBtn.click( fn = updateEstimation, outputs= extra_estimText ,inputs = [task_layers,task_frameDuration,task_endCondition,task_playMode] )


        
        return [task_layers, task_frameDuration, task_endCondition, task_playMode]

    # Function to show the script
    def show(self, is_img2img):
        return True

    # Function to run the script
    def run(self, p,task_layers, task_frameDuration, task_endCondition, task_playMode):
        # Make a process_images Object        
        return main(p,task_layers, task_frameDuration, task_endCondition, task_playMode)

#---------------------------------------------------------------------