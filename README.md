# liliths-throne-localization
该项目致力于[“Lilith's Throne”(莉莉丝的王座)](https://github.com/Innoxia/liliths-throne-public)的汉化计划，并提供了一步到位的源码下载、字典下载、字典更新、条目提取、源码替换方法。

目前计划每天UTC 12:40进行自动打包生成jar，供汉化测试使用，支持windows和linux。

## 使用方法
### 打包jar下载
点击右侧“Releases”选择最新且对应操作系统的版本下载，并安装openjdk17以上的版本，设置路径，进行游玩。如不清楚，请百度“如何打开jar文件”。

当前Windows可以直接解压后点击exe文件开始游戏，**请注意不要使用中文路径**，会导致路径识别问题！

目前支持：
 - Windows(64位 32位)
 - Linux(x64 aarch64)
 - Mac(x64 aarch64)

在此附上使用手机游玩的[可能性方案](https://github.com/Agreous/liliths-throne-on-android#readme)，比较复杂，且对手机性能有一定要求。

### 自行编译
#### 安装依赖
通过
``` shell
pip install -r requirements.txt
```
安装所需依赖

#### 应用汉化
首先打开**main.py**在PARATRANZ_ACCESS_TOKEN处填入从paratranz获取的API TOKEN(个人页面-设置)，再使用（根据系统或所用终端）
``` bash
bash ./bash.sh
```
或
``` powershell
./bash.bat
```
* 由于以上两种方法需要依靠git的submodule，在clone仓库时会出现网络连接问题，若无法使用，也可以选择直接执行
``` shell
# 主体项目
python main.py
# mod项目
python main.py --target mod
```

#### 编译文件
若希望同时获得exe文件，请在编译前先运行
``` shell
python exe_bundle.py
```

程序运行完毕后，进入liliths-throne-public-dev路径下，通过命令完成编译。
``` shell
cd liliths-throne-public
mvn package
```

 - 使用maven编译请先前往[官方网站](https://maven.apache.org/install.html)下载并配置路径。
     - 一般来说maven编译时需要下载依赖，且速度较慢，推荐国内用户设置镜像
	 - 具体方法可以参见[这里](https://developer.aliyun.com/mirror/maven)
	 - 在此提供一个华为的镜像源，找到maven安装根目录下的"*./conf/setting.xml*"，在"mirrors"标签下添加：
```
<mirror>  
	<id>huaweicloud</id>
	<name>huawei Maven</name>
	<url>http://repo.huaweicloud.com/repository/maven/</url>
	<mirrorOf>central</mirrorOf>
</mirror>  
```
 - 使用其他方法编译请详见源码中的*lilithsThroneBuildTutorial.md*
 - 该版本推荐使用java17及以上版本编译，而非原仓库推荐的java8。
     - [openjdk微软源](https://learn.microsoft.com/zh-cn/java/openjdk/download)
	 - [openjdk Oracle源](https://www.oracle.com/java/technologies/downloads/#jdk17-windows)