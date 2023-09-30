# liliths-throne-localization
该项目致力于“Lilith's Throne”(莉莉丝的王座)的汉化计划，并提供了一步到位的源码下载、字典下载、字典更新、条目提取、源码替换方式。

目前计划每天UTC 12:30进行自动打包生成jar，供汉化测试使用，支持windows和linux。

## 使用方法
### 打包jar下载
点击右侧“Releases”选择最新且对应操作系统的版本下载，并安装openjdk17以上的版本，设置路径，进行游玩。如不清楚，请百度“如何打开jar文件”。

### 自行编译
通过
``` shell
pip install -r requirements.txt
```
安装所需依赖

首先打开**main.py**在PARATRANZ_ACCESS_TOKEN处填入从paratranz获取的API TOKEN(个人页面-设置)，再使用
``` shell
python main.py
```
程序运行完毕后，进入liliths-throne-public-dev路径下，通过命令
``` shell
mvn package
```
完成编译。该版本推荐使用java17及以上版本编译，而非原仓库推荐的java8。