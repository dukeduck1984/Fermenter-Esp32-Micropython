#
# Web server powered by MicroWebSrv (a frozen module in Loboris firmware for ESP32)
#
from microWebSrv import MicroWebSrv
import _thread


class HttpServer:
    def __init__(self, process_obj):
        self.process = process_obj

    def start(self):
        process = self.process

        # Define the web routes and functions
        @MicroWebSrv.route('/')
        def index_get(httpClient, httpResponse):
            if process.is_started():
                # TODO
                # 1 Show stage status
                target_temp, stage_status, stage_percent = process.get_stage_info()

                # 2 Stage form should be disabled
                # 3 Load stage button & start button should be disabled
                pass
            else:
                # TODO
                # 1. Stage form is enabled for entering info
                # 2. Load stage button & start button is enabled
                pass
            
            if process.is_loaded():
                # TODO
                # Show stages info in the form
                num_stages = len(process.fermentation_stages)
                pass
            else:
                # TODO
                # Leave stages form blank
                pass
            
            with open('index.html', 'r') as html:
                content = html.read()
            httpResponse.WriteResponseOk(headers=None,
                                        contentType='text/html',
                                        contentCharset='UTF-8',
                                        content=content)


        @MicroWebSrv.route('/', 'POST')
        def index_post(httpClient, httpResponse):
            """Load fermentation stages by Http Post method

            Showing the loaded stages in the form
            
            Arguments:
                httpClient {[type]} -- [description]
                httpResponse {[type]} -- [description]
            """

            formData = httpClient.ReadRequestPostedFormData()
            num_stages = len(formData) / 2
            
            # TODO
            # Get stage info from formData and turn it to a list
            # then process.load_stages(list)
            # 


        @MicroWebSrv.route('/settings')
        def settings_get(httpClient, httpResponse):

            # TODO
            # 1. open config.json and read settings
            # 2. fill the settings form with default settings
            pass
        

        @MicroWebSrv.route('/settings', 'POST')
        def settings_post(httpClient, httpResponse):
            formData = httpClient.ReadRequestPostedFormData()

            # TODO
            # 1. Get new settings from formData and turn it to a dict
            # 2. Save the new setting by overwriting the config.json
            # 


        @MicroWebSrv.route('/start')
        def handlerFuncEdit(httpClient, httpResponse):
            # start the fermentation
            process.start()
            httpResponse.WriteResponseOk(headers=None,
                                        contentType='text/html',
                                        contentCharset='UTF-8',
                                        content='')

        # Initialize the Web server
        app = MicroWebSrv(webPath='/flash')
        app.Start()  # Starts the server
