# find2rename
find&amp;rename images file name to previous/查找并将照片重命名为原来的名字

# 语言支持/Language Support
| Language | Supported?  |
| -------- | ----------- |
| 中文     | √ |
| English  | × |
| 日本語   | × |

# 原理？

这个程序会使用SSIM（结构相似性）算法，对源文件夹内的图片文件和待重命名文件夹内的图片文件进行比较，以便找回待重命名文件夹中图片的文件名

例如：你通过社交媒体或工具发送你的照片给模特进行修图或其他操作，完成后模特通过社交媒体或工具发回给你，此时文件名很大概率已经发生改变

为方便管理和溯源，可以使用这个程序来将这些照片重命名为原来的名字


# 使用
**Release版本将在之后发布，可到issue催更**

使用源码的同学请确保自己有一定的独立思考能力和解决相关问题的能力，建议`Python版本>3.10`

### 下载
下载主程序`find2rename.py`、环境配置文件`requirements.txt`和配置文件`Config_find2rename.py`

配置文件**不会**在第一次运行主程序且工作路径下无配置文件时自动生成

### 安装第三方库

打开命令提示符/终端，进入主程序所在目录

假设你下载到了`C:\Users\olaf\Download`，在命令行分别执行：

    cd C:\Users\olaf\Download
    pip install -r requirements.txt

先不要关闭命令行，看下一步

### 修改配置文件

配置文件中各个变量名称和用途如下，也可参考配置文件内注释，注意，不要删除/修改配置文件中的引号/中括号/大括号



### 运行

如果使用MySQL/MariaDB，确保已经创建了数据库，数据表会在运行程序时自动创建

在命令行执行(注意：Linux/macOS用户可能需要将`python`改为`python3`)：

    python find2rename.py 

可能可以通过双击`fileHash.py`来运行程序

