from microWebSrv import MicroWebSrv
import machine
import ujson
import utime


class HttpServer:
    def __init__(self, process_obj, wifi_obj, rtc_obj, user_settings_dict):
        self.process = process_obj
        self.wifi = wifi_obj
        self.rtc = rtc_obj
        self.settings = user_settings_dict
        self.app = None
        self.hydrometer_data = {
            'originalGravity': None,
            'currentGravity': None,
            'batteryLevel': None,
        }
        self.set_temp = None
        self.chamber_temp = None
        self.wort_temp = None
        self.time_mark = None

    def start(self):
        process = self.process
        wifi = self.wifi
        rtc = self.rtc
        settings = self.settings
        this = self

        @MicroWebSrv.route('/connecttest')
        def test_get(httpClient, httpResponse):
            """
            测试前端和后端之间的网络连接
            """
            httpResponse.WriteResponseOk()

        # Define the web routes and functions
        @MicroWebSrv.route('/overview')
        def overview_get(httpClient, httpResponse):
            """
            提供首页所有数据显示，前端每1分钟请求1次
            """
            brewery_name = settings['breweryName']
            wifi_connected = wifi.is_connected()
            real_date = rtc.get_localdate()
            real_time = rtc.get_localtime()
            basic_info = {
                'breweryName': brewery_name,
                'wifiIsConnected': wifi_connected,
                'realDate': real_date,
                'realTime': real_time,
            }
            process_info = process.get_process_info()
            overview = basic_info.copy()
            overview.update(process_info)
            data = {
                'fermenter_overview': overview,
                'hydrometer_data': this.hydrometer_data
            }
            this.set_temp = process_info.get('setTemp')
            this.chamber_temp = process_info.get('chamberTemp')
            this.wort_temp = process_info.get('wortTemp')
            this.time_mark = utime.time()
            httpResponse.WriteResponseJSONOk(obj=data, headers=None)

        @MicroWebSrv.route('/fermentation', 'POST')
        def fermentation_post(httpClient, httpResponse):
            """
            前台向后台提交发酵步骤数据，并且开始发酵过程
            """
            json = httpClient.ReadRequestContentAsJSON()
            # fermentationSteps = ujson.loads(json)['fermentationSteps']
            beerName = json['beerName']
            fermentationSteps = json['fermentationSteps']
            try:
                process.set_beer_name(beerName)
                process.load_steps(fermentationSteps)
                process.start()
            except:
                # throw 500 error code
                httpResponse.WriteResponseInternalServerError()
            else:
                httpResponse.WriteResponseOk()

        @MicroWebSrv.route('/abort')
        def abort_get(httpClient, httpResponse):
            try:
                process.abort()
            except:
                # throw 500 error code
                httpResponse.WriteResponseInternalServerError()
            else:
                httpResponse.WriteResponseOk()

        @MicroWebSrv.route('/settings')
        def settings_get(httpClient, httpResponse):
            """
            从后台读取设置参数
            """
            wifi_list = wifi.scan_wifi_list()
            temp_sensor_list = process.fermenter_temp_ctrl.chamber_sensor.ds_obj.get_device_list()
            # open user_settings.json and read settings
            with open('user_settings.json', 'r') as f:
                settings_dict = ujson.load(f)
            wort_sensor_dev_num = settings_dict.get('wortSensorDev')
            chamber_sensor_dev_num = settings_dict.get('chamberSensorDev')
            wort_sensor_rom_code = ''
            chamber_sensor_rom_code = ''
            for sensor_dict in temp_sensor_list:
                detail_list = sensor_dict.values()
                if wort_sensor_dev_num in detail_list:
                    wort_sensor_rom_code = sensor_dict.get('label')
                elif chamber_sensor_dev_num in detail_list:
                    chamber_sensor_rom_code = sensor_dict.get('label')

            wort_sensor_dev = {
                'value': wort_sensor_dev_num,
                'label': wort_sensor_rom_code
            }
            chamber_sensor_dev = {
                'value': chamber_sensor_dev_num,
                'label': chamber_sensor_rom_code
            }
            settings_added = {
                'wifiList': wifi_list,
                'wortSensorDev': wort_sensor_dev,
                'chamberSensorDev': chamber_sensor_dev,
                'tempSensorList': temp_sensor_list
            }
            settings_combined = settings_dict.copy()
            settings_combined.update(settings_added)
            # settings_json = ujson.dumps(settings_combined)
            httpResponse.WriteResponseJSONOk(obj=settings_combined, headers=None)
            # httpResponse.WriteResponseOk(
            #     headers=None,
            #     contentType="application/json",
            #     contentCharset="UTF-8",
            #     content=settings_json
            # )

        @MicroWebSrv.route('/settings', 'POST')
        def settings_post(httpClient, httpResponse):
            """
            向后台保存设置参数，并且重启ESP32
            """
            # json = httpClient.ReadRequestContentAsJSON()
            # settings_dict = ujson.loads(json)
            settings_dict = httpClient.ReadRequestContentAsJSON()
            settings_dict['wortSensorDev'] = settings_dict['wortSensorDev']['value']
            settings_dict['chamberSensorDev'] = settings_dict['chamberSensorDev']['value']
            try:
                with open('user_settings.json', 'w') as f:
                    ujson.dump(settings_dict, f)
            except:
                httpResponse.WriteResponseInternalServerError()
            else:
                httpResponse.WriteResponseOk()

        @MicroWebSrv.route('/reboot')
        def reboot_get(httpClient, httpResponse):
            tim = machine.Timer(-1)
            try:
                tim.init(period=3000, mode=machine.Timer.ONE_SHOT, callback=lambda t: machine.reset())
            except:
                httpResponse.WriteResponseInternalServerError()
            else:
                httpResponse.WriteResponseOk()

        @MicroWebSrv.route('/wifi')
        def wifi_get(httpClient, httpResponse):
            """
            获取WIFI热点列表，用于刷新热点列表
            """
            wifi_list = wifi.scan_wifi_list()
            wifi_dict = {'wifiList': wifi_list}
            # wifi_json = ujson.dumps(wifi_dict)
            httpResponse.WriteResponseJSONOk(obj=wifi_dict, headers=None)
            # httpResponse.WriteResponseOk(
            #     headers=None,
            #     contentType="application/json",
            #     contentCharset="UTF-8",
            #     content=wifi_json
            # )

        @MicroWebSrv.route('/wifi', 'POST')
        def wifi_post(httpClient, httpResponse):
            """
            连接WIFI热点，连接成功后同步RTC时钟
            """
            # wifi_detail_json = httpClient.ReadRequestContentAsJSON()
            # wifi_dict = ujson.loads(wifi_detail_json)
            wifi_dict = httpClient.ReadRequestContentAsJSON()
            new_ip = wifi.sta_connect(wifi_dict['ssid'], wifi_dict['pass'])
            if new_ip:
                if not rtc.is_synced():
                    rtc.sync()
                # 200
                httpResponse.WriteResponseOk()
            else:
                # throw 500 error code
                httpResponse.WriteResponseInternalServerError()

        @MicroWebSrv.route('/tempsensors', 'POST')
        def temp_post(httpClient, httpResponse):
            """
            获取温度传感器读数
            """
            # 获取前端发来的设备序号
            sensor_dict = httpClient.ReadRequestContentAsJSON()
            new_wort_dev_num = sensor_dict.get('wortSensorDev').get('value')
            new_chamber_dev_num = sensor_dict.get('chamberSensorDev').get('value')
            # 获取温感对象实例
            wort_sensor = process.fermenter_temp_ctrl.wort_sensor
            chamber_sensor = process.fermenter_temp_ctrl.chamber_sensor
            # 更新温感设备序号
            wort_sensor.update_device_num(new_wort_dev_num)
            chamber_sensor.update_device_num(new_chamber_dev_num)
            try:
                # 测量温度
                wort_temp = wort_sensor.read_temp()
                chamber_temp = chamber_sensor.read_temp()
            except:
                # throw 500 error code
                httpResponse.WriteResponseInternalServerError()
            else:
                temp_dict = {
                    'wortTemp': wort_temp,
                    'chamberTemp': chamber_temp
                }
                httpResponse.WriteResponseJSONOk(obj=temp_dict, headers=None)

        @MicroWebSrv.route('/gravity', 'POST')
        def gravity_post(httpClient, httpResponse):
            json = httpClient.ReadRequestContentAsJSON()
            sg = json['sg']
            battery = json['battery']
            this.hydrometer_data['currentGravity'] = sg
            this.hydrometer_data['batteryLevel'] = battery
            if this.hydrometer_data.get('originalGravity'):
                if float(this.hydrometer_data['originalGravity']) < sg:
                    this.hydrometer_data['originalGravity'] = sg
            else:
                this.hydrometer_data['originalGravity'] = sg
            try:
                print('Hydrometer data received.')
                print('SG: ' + str(round(sg, 3)))
                print('Battery: ' + str(round(battery, 1)) + '%')
            except:
                pass
            httpResponse.WriteResponseOk()

        @MicroWebSrv.route('/chart')
        def chart_get(httpClient, httpResponse):
            data = {
                'timeMark': this.time_mark,
                'setTemp': this.set_temp,
                'wortTemp': this.wort_temp,
                'chamberTemp': this.chamber_temp,
                'gravitySg': this.hydrometer_data.get('currentGravity')
            }
            httpResponse.WriteResponseJSONOk(obj=data, headers=None)

        # Initialize the Web server
        self.app = MicroWebSrv(webPath='/sd/www')
        self.app.Start(threaded=True)  # Starts the server

    def stop(self):
        if self.app:
            self.app.Stop()

    def is_started(self):
        if self.app:
            return self.app.IsStarted()
        else:
            return False
