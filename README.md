# fermenter_esp32_micropython
Convert a fridge into a beer brewing fermenter with an ESP32 powered by MicroPython Loboris fork

### 首页
1. 显示冰箱环境温度
2. 显示麦芽汁液体温度
3. 显示目标温度
4. 显示加热器、制冷压缩机的工作状态
5. 当前工作状态：待机、发酵中、发酵完成
6. 待机时：可编辑发酵步骤，包括发酵时长（天）、发酵目标温度。至少需要一个发酵步骤才能启动发酵工作状态。
7. 发酵中：显示全部发酵步骤，标识出已完成、进行中、未完成的步骤；结合进度条显示完成进度百分比。
8. 发酵完成：弹出提示框表示已经完成。
9. 记录温度和时间数据到tf卡，显示温度折线图

### 设置页
1. 设置ESP32自己的SSID
2. 选择并连接WIFI热点
3. 设置温度传感器编号
