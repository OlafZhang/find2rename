from Config_find2rename import *
from colorama import init,Fore
from rich.progress import Progress,TextColumn,TimeElapsedColumn,TimeRemainingColumn
from skimage.metrics import structural_similarity as compare_ssim
from PIL import Image  
import numpy as np
import os,time,random,sys,signal,threading,psutil,copy,base64
init(autoreset=True)

cpuUsage = 0.0
pairedFile = 0
unpairFile = 0
pruningCount = 0
nowFileCount = 0
calcFileCount = 0
workItem = []
needRenameFileList = []
sourceFileFileList = []
# "待匹配文件名"："匹配文件名","可能性","是否找到",
# 可能性小于0表示没找到，大于等于0表示找到可能匹配的文件名
globalFileDict = {}
isError = False
threadWorker = 1 if threadWorker <= 0 else 1000 if threadWorker >= 1000 else threadWorker
needRenameFoldersName = needRenameFoldersName.replace("\\","/")
sourceFileFoldersName = sourceFileFoldersName.replace("\\","/")
if not os.path.exists(needRenameFoldersName):
    print(f"待重命名文件夹路径'{needRenameFoldersName}'路径有误，请检查")
    isError = True
if not os.path.exists(sourceFileFoldersName):
    print(f"源文件夹路径'{sourceFileFoldersName}'路径有误，请检查")
    isError = True
if isError:
    sys.exit(1)

def resize_image(image_path, target_size):  
    with Image.open(image_path) as img:  
        img = img.resize(target_size, Image.BILINEAR)  
        return img  
def compareImages_SSIM(img1Path,img2Path,zoom=1):
    zoom = 1 if zoom <= 0 or zoom > 1 else zoom
    width1, height1 = Image.open(img1Path).size
    width2, height2 = Image.open(img2Path).size
    if (width1 >= height1) != (width2 >= height2):
        return float(-1.0)
    target_size = (int(min(width1, width2) * zoom), int(min(height1, height2) * zoom)) 
    img1 = np.array(resize_image(img1Path, target_size).convert('L'))
    img2 = np.array(resize_image(img2Path, target_size).convert('L'))
    ssim = compare_ssim(img1,img2,win_size=7,full=False,multichannel=False)
    return float(ssim)
def getFileName(path):
    return str(path).split("/")[-1]
def renameFile(needRenameFoldersName,rollback=False):
    global globalFileDict,prefix,postfix,threshold
    globalFileDictTEMP = copy.deepcopy(globalFileDict)
    for x,y in globalFileDictTEMP.items():
        if not ifPossibleThenRename and y[1] < threshold:
            continue
        index = 0
        extension = os.path.splitext(str(x))[-1]
        a = f"{needRenameFoldersName}/{x}"
        b = f"{needRenameFoldersName}/{prefix}{str(y[0]).replace(extension,"")}{postfix}{extension}"
        if a == b:
            print(f"{Fore.CYAN}忽略{Fore.RESET} {str(a).replace(needRenameFoldersName+"/","")}")
            continue
        while os.path.exists(b) and not rollback:
            index += 1
            globalFileDict[x] = [f"{str(y[0]).replace(extension,"")}_{index}{extension}",y[1],y[2]]
            b = f"{needRenameFoldersName}/{prefix}{str(y[0]).replace(extension,"")}_{index}{postfix}{extension}"
        try:
            if rollback:
                a,b = b,a
            print(("%s --> %s ")%(str(a).replace(str(needRenameFoldersName)+str("/"),""),str(b).replace(str(needRenameFoldersName)+str("/"),"")),end="")
            os.rename(a,b)
            print(f"{Fore.GREEN}成功{Fore.RESET}" if index == 0 else f"{Fore.YELLOW}成功(防冲突){Fore.RESET}")
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"{Fore.RED}失败{Fore.RESET}")
            print(str(exc_type)+"\n"+str(exc_value))
    return
def killThread(signum, frame):
    if os.path.exists("result.html"):
        os.remove("result.html")
    print("线程被中止")
    sys.exit(0)
def getIndex(intIndex):
    return f"00{intIndex}" if intIndex < 10 else f"0{intIndex}" if intIndex < 100 else f"{intIndex}"
def compareMainThread(thisItemList):
    global globalFileDict,nowFileCount,calcFileCount,pruningCount
    for i in thisItemList: 
        if globalFileDict[getFileName(i[0])][2] == True:
            nowFileCount+=1
            pruningCount+=1
            continue
        result = compareImages_SSIM(i[0],i[1],zoom=zoomLevel)
        if float(result) >= 0:
            calcFileCount+=1
        else:
            pruningCount+=1
        if float(result) >= float(threshold):
            globalFileDict[getFileName(i[0])] = [getFileName(i[1]),result,True]
            print(str(("%s --> %s，可能性%s")%(getFileName(i[0]),getFileName(i[1]),str(result)[0:5])))
        else:
            if result > globalFileDict[getFileName(i[0])][1]:
                globalFileDict[getFileName(i[0])] = [getFileName(i[1]),result,False]
        nowFileCount+=1
def cpuMonitor():
    global cpuUsage
    try:
        while True:
            cpuUsage = psutil.cpu_percent(interval=1)
    except Exception as ex:
        cpuUsage = f"{Fore.YELLOW}ERROR{Fore.RESET}"
        print(ex)
def timeFormat(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    returnFormat = ""
    if hours != 0:
        returnFormat += f"{int(hours)}小时"
    if minutes != 0:
        returnFormat += f"{int(minutes)}分"
    if seconds != 0:
        returnFormat += f"{int(seconds)}秒"
    return returnFormat
def askYou(question):
    while True:
        userInput = input(f"{Fore.YELLOW}{question}{Fore.RESET}(y/n)：")
        if userInput.lower() == "y" or userInput.lower() == "yes":
            return True
        elif userInput.lower() == "n" or userInput.lower() == "no":
            return False
def htmlRender():
    global globalFileDict
    htmlFile = open("result.html","w",encoding="utf-8")
    htmlFile.write('<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>重命名结果预览</title>\n</head>\n<body style="background-color: #fafafa">\n')
    htmlFile.write('<div align="center"><h3>已匹配</h3></div>\n')
    for x,y in globalFileDict.items():
        if y[2]:
            htmlFile.write(f'    <div align="center">\n        <img src="{needRenameFoldersName}/{x}" width="20%">\n')
            htmlFile.write(f'        <img src="{sourceFileFoldersName}/{y[0]}" width="20%" height="20%">\n    </div>\n')
            htmlFile.write(f'    <p align="center">[<font color="#00cf2c">{str(y[1])[0:5]}</font>] {x} --> {y[0]}"</p>\n')
    htmlFile.write('<div align="center"><h3>可能结果</h3></div>\n')
    for x,y in globalFileDict.items():
        if float(y[1]) >= 0.0 and not y[2]:
            htmlFile.write(f'    <div align="center">\n        <img src="{needRenameFoldersName}/{x}" width="20%">\n')
            htmlFile.write(f'        <img src="{sourceFileFoldersName}/{y[0]}" width="20%" height="20%">\n    </div>\n')
            htmlFile.write(f'    <p align="center">[<font color="#ffcc00">{str(y[1])[0:5]}</font>] {x} --> {y[0]}</p>\n')
    htmlFile.write('</body>\n</html>')
    htmlFile.close()
    os.system("result.html")
    return
signal.signal(signal.SIGINT, killThread)

for i in os.listdir(sourceFileFoldersName):
    if os.path.isfile(f"{sourceFileFoldersName}/{i}") and str(str(i).split(".")[-1]).lower() in fileSupport:
        sourceFileFileList.append(f"{sourceFileFoldersName}/{i}")
for i in os.listdir(needRenameFoldersName):
    if os.path.isfile(f"{needRenameFoldersName}/{i}") and str(str(i).split(".")[-1]).lower() in fileSupport:
        needRenameFileList.append(f"{needRenameFoldersName}/{i}")
        globalFileDict[str(i)] = ["",-1.0,False]

cpuMonitorThread = threading.Thread(target=cpuMonitor, args="")
cpuMonitorThread.daemon=True
cpuMonitorThread.start()
for x in needRenameFileList:
    for y in sourceFileFileList:
        workItem.append([x,y])
workItemCount = len(workItem)
for i in range(0,10):
    random.shuffle(workItem)
while workItemCount % threadWorker != 0:
    workItemCount += 1
for i in range(0,threadWorker):
    exec(f"workItem_{getIndex(i)}=[]")
for i in range(0,workItemCount,threadWorker):
    try:
        for index in range(0,threadWorker):
            exec(f"workItem_{getIndex(index)}.append(workItem[i+{index}])")
    except IndexError:
        break
for i in range(0,threadWorker):
    exec(f"t{getIndex(i)}=threading.Thread(target=compareMainThread, args=(workItem_{getIndex(i)},))")
    exec(f"t{getIndex(i)}.daemon=True")
    exec(f"t{getIndex(i)}.start()")

start_time = time.time()
with Progress(TextColumn("运行SSIM结构相似性算法  "+"[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),TimeElapsedColumn()) as progress:
    check1_tqdm = progress.add_task(description="", total=len(workItem))
    lastNowFileCount = 0
    while len(workItem) > nowFileCount:
        catch_nowFileCount = nowFileCount
        cpuUsageDisplay = f"{Fore.GREEN}{cpuUsage}%{Fore.RESET}" if int(cpuUsage) <= 60 else f"{Fore.YELLOW}{cpuUsage}%{Fore.RESET}" if int(cpuUsage) < 80 else f"{Fore.RED}{cpuUsage}%{Fore.RESET}"
        progress.update(check1_tqdm, description=f"线程数：{threadWorker}  CPU：{cpuUsageDisplay}  已计算：{calcFileCount}  理论：{len(workItem)}  已减枝：{pruningCount}", refresh=True)
        progress.advance(check1_tqdm, advance=catch_nowFileCount-lastNowFileCount)
        lastNowFileCount = catch_nowFileCount
        time.sleep(0.01)
end_time = time.time()
os.system("cls")
htmlRender()
print("汇总")
for x,y in globalFileDict.items():
    pairedFile = pairedFile+1 if y[1] > 0.0 and y[2] == True else pairedFile
    unpairFile = unpairFile+1 if y[2] == False else unpairFile
if pairedFile > 0:
    print("匹配的文件：")
    for x,y in globalFileDict.items():
        if y[1] > 0.0 and y[2] == True:
            print(f"[{Fore.GREEN}{str(y[1])[0:5]}{Fore.RESET}] {x} --> {y[0]}")
    print(f"匹配的文件数量：{Fore.GREEN}{pairedFile}{Fore.RESET}")
else:
    print(f"{Fore.RED}未找到匹配的文件{Fore.RESET}")
if unpairFile > 0:
    print("未匹配文件：")
    for x,y in globalFileDict.items():
        if y[2] == False:
            print(f"{x}(可能匹配的文件名：{y[0]}，相似度为 {str(y[1])[0:5]})" if y[1] >= 0.0 else f"{x}")
    print(f"未匹配文件数量：{Fore.RED}{unpairFile}{Fore.RESET}")
else:
    print(f"{Fore.GREEN}无未匹配的文件{Fore.RESET}")
print(f"计算文件对/理论计算文件对/已减枝文件对：{calcFileCount}/{len(workItem)}/{pruningCount}")
print(f"运行用时：{timeFormat(end_time-start_time)}\n相似阈值：{Fore.YELLOW}{threshold}{Fore.RESET}\n缩放等级：{Fore.YELLOW}{zoomLevel}{Fore.RESET}")
print(f"待重命名/已匹配/未匹配：{len(needRenameFileList)}/{pairedFile}/{unpairFile}")
showPrefix = f"是否加重命名前缀：{Fore.YELLOW}否{Fore.RESET}" if prefix == "" else f"是否加重命名前缀：{Fore.YELLOW}是{Fore.RESET}({prefix})"
showPostfix = f"是否加重命名后缀：{Fore.YELLOW}否{Fore.RESET}" if postfix == "" else f"是否加重命名后缀：{Fore.YELLOW}是{Fore.RESET}({postfix})"
print(f"{showPrefix}\n{showPostfix}")
if pairedFile > 0:
    print("重命名结果预览HTML页面已生成并打开")
    result = askYou("执行匹配文件和可能文件的修改？") if ifPossibleThenRename and unpairFile!=0 else askYou("执行匹配文件的修改？")
    if result:
        renameFile(needRenameFoldersName)
        result = askYou("修改完毕，是否执行回滚？")
        if result:
            renameFile(needRenameFoldersName,rollback=True)
if os.path.exists("result.html"):
    os.remove("result.html")
print("程序退出")
