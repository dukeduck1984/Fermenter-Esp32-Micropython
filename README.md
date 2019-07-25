# fermenter_esp32_micropython
Convert a fridge into a beer brewing fermenter with an ESP32 powered by MicroPython Loboris fork

### 首页
1. 显示冰箱环境温度（mdi-fridge-outline）
2. 显示麦芽汁液体温度（mdi-beaker）
3. 显示目标温度（mdi-target）
4. 显示加热器（mdi-fire）、制冷压缩机（mdi-snowflake）的工作状态
5. 显示当前工作状态：待机(mdi-power-standby、发酵中(mdi-progress-clock)、发酵完成(mdi-progress-check)
6. 显示实际时间RTC（年月日；具体时间）(mdi-clock-outline)
7. 显示WIFI热点连接状态(mdi-wifi-off, mdi-wifi)
- 显示糖度比重数据（mdi-test-tube）
8. 待机时：可编辑所酿酒的名称（mdi-beer）、发酵步骤，包括发酵时长（天）（mdi-calendar-clock）、发酵目标温度（mdi-temperature-celsius）。至少需要一个发酵步骤才能启动发酵工作状态。
9. 发酵中：显示全部发酵步骤，标识出已完成（mdi-check-circle）、进行中（大于零小于十五mdi-circle-slice-1，十五到三十mdi-circle-slice-2，三十到四十五mdi-circle-slice-3，四十五到五十五mdi-circle-slice-4，五十五到七十mdi-circle-slice-5，七十到八十五mdi-circle-slice-6，大于八十五小于一百mdi-circle-slice-7）、未完成（mdi-circle-outline）的步骤；结合进度条显示当前步骤完成进度百分比，显示当前步骤剩余天数和小时数。
10. 发酵完成：弹出提示框表示已经完成。
- 记录温度和时间数据到tf卡，显示温度折线图
- 记录糖度比重数据，显示比重折线图

### 设置页
1. 设置ESP32自己的SSID
2. 选择并连接WIFI热点
3. 设置温度传感器编号
4. 设置酒厂名称

### API
- /overview
-- GET
