# Fermenter-Esp32-MicroPython
Convert a fridge into a beer brewing fermenter with an ESP32 powered by MicroPython ESP32 port (https://github.com/micropython/micropython)

### 首页
- [X] 显示冰箱环境温度（mdi-fridge-outline）
- [X] 显示麦芽汁液体温度（mdi-beaker）
- [X] 显示目标温度（mdi-target）
- [X] 显示加热器（mdi-fire）、制冷压缩机（mdi-snowflake）的工作状态
- [X] 显示当前工作状态：待机(mdi-power-standby、发酵中(mdi-progress-clock)、发酵完成(mdi-progress-check)
- [X] 显示实际时间RTC（年月日；具体时间）(mdi-clock-outline)
- [X] 显示WIFI热点连接状态(mdi-wifi-off, mdi-wifi)
- [X] 显示糖度比重数据（mdi-test-tube）
- [X] 待机时：可编辑所酿酒的名称（mdi-beer）、发酵步骤，包括发酵时长（天）（mdi-calendar-clock）、发酵目标温度（mdi-temperature-celsius）。至少需要一个发酵步骤才能启动发酵工作状态。
- [X] 发酵中：显示全部发酵步骤，标识出已完成（mdi-check-circle）、进行中（大于零小于十五mdi-circle-slice-1，十五到三十mdi-circle-slice-2，三十到四十五mdi-circle-slice-3，四十五到五十五mdi-circle-slice-4，五十五到七十mdi-circle-slice-5，七十到八十五mdi-circle-slice-6，大于八十五小于一百mdi-circle-slice-7）、未完成（mdi-circle-outline）的步骤；结合进度条显示当前步骤完成进度百分比，显示当前步骤剩余天数和小时数。
- [X] 发酵完成：弹出提示框表示已经完成。
- [X] 每20分钟更新温度、比重和时间数据到折线图上，数据保存在sessionStorage
- [X] 每20分钟记录1次糖度比重数据，显示比重折线图(从比重计端实现)
- [X] 所发酵的啤酒名称beerName也回传到后台进行记录
- [X] 增加意外重启后自动恢复执行剩下的发酵步骤。如：每5分钟保存一次发酵信息：全部发酵步骤，正在发酵的步骤及剩余时间，未完成的步骤 etc.
- [X] 支持通过MQTT定时向第三方物联网平台发送发酵温度和比重数据

### 设置页
- [X] 设置ESP32自己的SSID
- [X] 选择并连接WIFI热点
- [X] 设置温度传感器编号
- [X] 设置酒厂名称

### API
#### /connecttest
* GET  // 每5秒联系一次后台，确认通讯正常

#### /overview
* GET  // 每1分钟从后台更新一次数据
```
{
    breweryName: "豚鼠精酿",  // string, 酒厂名称
    machineStatus: "standby",  // string, 机器状态，standby待机，running正在发酵，done发酵完成
    wifiIsConnected: true,  // boolean, 是否连接上了WIFI热点
    realDate: "2019/7/25"  // string, 当前日期
    realTime: "16:06",  // string, 当前时间
    setTemp: 20.1,  // number, 目标设定温度
    wortTemp: 21.4,  // number, 当前麦芽汁温度
    chamberTemp: 18.3,  // number, 当前冰箱内环境温度
    isHeating: false,  // boolean, 加热器是否开启
    isCooling: true,  // boolean, 制冷压缩机是否开启
    beerName: "Two-Hearted IPA",  // string, 所酿啤酒的名称
    fermentationSteps: [  // array, 发酵步骤
      {
        days: 2,  // number, 天数
        temp: 18.2  // number, 温度
      },
      {
        days: 14,
        temp: 20.5
      },
      {
        days: 7,
        temp: 22
      }
    ],
    currentFermentationStepIndex: 0,  // number, 当前发酵步骤的index，从0开始计
    currentFermentationStepPercentage: 74  // number, 当前发酵步骤的完成百分比
    hydrometerData: {
      originalGravity: 1.035,
      currentGravity: 1.017
      batteryLevel: 60
    }
}
```

#### /fermentation
* POST  // 向后端发送发酵步骤，并开始发酵过程
```
{
  beerName: "Two-hearted IPA",
  fermentationSteps: [  // array, 发酵步骤
    {
      days: 2,  // number, 天数
      temp: 18.2  // number, 温度
    },
    {
      days: 14,
      temp: 20.5
    },
    {
      days: 7,
      temp: 22
    }
  ],
}
```

#### /settings
* GET  // 从后端获取设置信息
```
{
  breweryName: "豚鼠精酿",  // string, 酒厂名称
  apSsid: "Fermenter",  // string, ESP32自己的WIFI信号SSID
  wifi: {  // object, 要连接的wifi热点ssid和连接密码
    ssid: "SSID1",
    pass: "thisissecret"
  }
  wifiList: [  // array, ESP32搜索到的WIFI热点列表
    "SSID0",  // string
    "SSID1",
    ...,
    "SSID9"
  ],
  wortSensorDev: {  // object
    value: 0,  // number，传感器序号
    label: "DS18B20XX02"  // string, 传感器编码
  },
  chamberSensorDev: {
    value: 1,  // number，传感器序号
    label: "DS18B20XD51"  // string, 传感器编码
  },
  tempSensorList: [  // array, 温度传感器列表
    {  // object
      value: 0,  // number，传感器序号
      label: "DS18B20XX02"  // string, 传感器编码
    },
    {
      value: 1,
      label: "DS18B20XD51"
    }
  ]
}
```
* POST  // 向后端发送设置信息
```
{
  breweryName: "豚鼠精酿",  // string, 酒厂名称
  apSsid: "Fermenter",  // string, ESP32自己的WIFI信号SSID
  wifi: {  // object, 要连接的wifi热点ssid和连接密码
    ssid: "SSID1",
    pass: "thisissecret"
  },
  wortSensorDev: {  // object
    value: 0,  // number，传感器序号
    label: "DS18B20XX02"  // string, 传感器编码
  },
  chamberSensorDev: {
    value: 1,  // number，传感器序号
    label: "DS18B20XD51"  // string, 传感器编码
  },
}
```

#### /wifi
* GET  // 刷新WiFi热点列表
```
{
    "wifiList": [
        "210",
        "ChinaNet-bAuq",
        "211",
        "209",
        "212",
        "236",
        "226",
        "202",
        "ChinaNet-JwDr",
        "208",
        "203",
        "225",
        "ChinaNet-4dct",
        "215",
        "ChinaNet-hums"
    ]
}
```
* POST  // 切换所连接的AP
```
{
    "ssid": "210",
    "pass": "88888888"
}
```

#### /tempsensors
* POST  // 重新设置ds18温感设备编号，并返回温度值
```
{
  "wortSensorDev": {
    "value": 1,
    "label": "0x28aa34e41813023b"
  },
  "chamberSensorDev": {
    "value": 0,
    "label": "0x28aaec0119130238"
  },
}
```

#### /actuator
* POST  // 手动打开或者关闭制冷压缩机或者制热板，主要用于测试
```
{
  "element": "heater",  // "cooler"
  "action": true  // false
}
```

#### /gravity
* POST  // 由比重计发送比重数据到发酵箱
```
{
  "currentGravity": 1.0123,
  "batteryLevel": 67.6,
  "updateIntervalSec": 1200
}
```

#### /chart
* GET  // 供前端绘制曲线图的数据，由前端定时读取，数据存在前端
```
{
  "timeMark": '2019/8/22 12:32',
  "setTemp": 21.5,
  "wortTemp": 21.9,
  "chamberTemp": 22.2,
  "gravitySg": 1.0123
}
```

#### /ftp
* GET // 开启FTP服务，方便程序源代码升级

#### /abort
* GET  // 终止发酵过程，删除恢复文件

#### /reboot
* GET  // 3秒后重新启动ESP32

### 使用echarts绘图，示例代码
```javascript
var option = {
    legend: {
        data: [
            {
                name: '麦芽汁温度',
                textStyle: {
                    color: 'orangered'
                }
            },
            {
                name: '发酵箱温度',
                textStyle: {
                    color: 'dodgerblue'
                }
            },
            {
                name: '目标温度',
                textStyle: {
                    color: 'rebeccapurple'
                }
            },
            {
                name: '麦芽汁比重',
                textStyle: {
                    color: 'limegreen'
                }
            },
        ]
    },
    tooltip: {
        trigger: 'axis',
    },
    dataset: {
        source: {
            'timeMark': ['2018/4/1 20:45', '2018/4/8 21:00', '2018/04/15 21:15', '2018/04/22 21:30', '2018/04/29 21:45'],
            'wortTemp': [19.2, 19.9, 20.3, 21.0, 21.5],
            'chamberTemp': [20.3, 20.9, 21.1, 21.7, 22.0],
            'setTemp': [22.5, 22.5, 22.5, 22.5, 22.5],
            'gravitySg': [null, null, 1.065, 1.055, 1.035]
        }
    },
    grid: {containLabel: true},
    xAxis: {
        type: 'time',
        offset: 20,
        name: '时 间',
        nameLocation: 'center',
        nameGap: 40,
        nameTextStyle: {
            fontSize: 20,
            fontWeight: 'bold'
        }
    },
    yAxis: [
        {
            type: 'value',
            name: '温 度',
            nameLocation: 'middle',
            nameRotate: 360,
            nameGap: 40,
            nameTextStyle: {
                fontSize: 20,
                fontWeight: 'bold'
            },
            min: (value) => {return Math.floor(value.min - 1)},
            max: (value) => {return Math.ceil(value.max + 1)},
            minInterval: 0.5,
            maxInterval: 1.5,
            axisLabel: {
                formatter: (value) => value.toFixed(1)
            }
        },
        {
            type: 'value',
            name: '比 重',
            nameLocation: 'middle',
            nameRotate: 360,
            nameGap: 45,
            nameTextStyle: {
                fontSize: 20,
                fontWeight: 'bold'
            },
            min: (value) => {return (value.min * 0.99).toFixed(3)},
            max: (value) => {return (value.max * 1.01).toFixed(3)},
            splitLine: {
                show: false,
            },
            minInterval: 0.002,
            maxInterval: 0.008,
            axisLabel: {
                formatter: (value) => value.toFixed(3)
            }
        }
    ],
    series: [
        {
            name: '麦芽汁温度',
            type: 'line',
            smooth: true,
            lineStyle: {
              width: 3,
              color: 'orangered'
            },
            itemStyle: {color: 'orangered'},
            yAxisIndex: 0,
            encode: {
                // Map the "amount" column to X axis.
                x: 'timeMark',
                // Map the "product" column to Y axis
                y: 'wortTemp'
            }
        },
        {
            name: '发酵箱温度',
            type: 'line',
            smooth: true,
            lineStyle: {
              width: 3,
              color: 'dodgerblue'
            },
            itemStyle: {color: 'dodgerblue'},
            yAxisIndex: 0,
            encode: {
                x: 'time',
                y: 'chamberTemp'
            }
        },
        {
            name: '目标温度',
            type: 'line',
            smooth: true,
            lineStyle: {
              width: 3,
              color: 'rebeccapurple'
            },
            itemStyle: {color: 'rebeccapurple'},
            yAxisIndex: 0,
            encode: {
                x: 'time',
                y: 'setTemp'
            }
        },
        {
            name: '麦芽汁比重',
            type: 'line',
            smooth: true,
            yAxisIndex: 1,
            lineStyle: {
              width: 3,
              color: 'limegreen'
            },
            itemStyle: {color: 'limegreen'},
            encode: {
                x: 'time',
                y: 'gravitySg'
            }
        }
    ]
};
```
