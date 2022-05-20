
import logging
import datetime
import serial
import serial.tools.list_ports as port_list
import threading
import time

class SerialMonitor():

    def __init__(self):
        logFormat = "[%(asctime)s] [%(levelname)-8s] [%(filename)-20s @ %(funcName)-15s:%(lineno)4s] %(message)s"
        logging.basicConfig(format=logFormat, level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.startTime = datetime.datetime.now()    # time of application start
        self.logger.debug("Starting app at %s ..." %self.startTime)

        # define default baudrate and port name (can be part of port's name)
        self.defaultBaudrate = 250000
        self.defaultPort = "COM4"

        # create empty list of available ports
        # ports info https://pyserial.readthedocs.io/en/latest/tools.html#serial.tools.list_ports.ListPortInfo
        # device, name, description
        self.allComPortsInfo = list(port_list.comports())
        print(self.allComPortsInfo)
        
        self._receivingThread = None
        self._runReadThread = False

        self._writeThread = None
        
        self._conn = None

    def getArduinoPort(self):
        ports = self.allComPortsInfo
        invalidPorts = ["/dev/tty.Bluetooth-Incoming-Port", "/dev/ttyAMA0"]
        for port in ports:
            validPort = True
            for invalidP in invalidPorts:
                if port.device == invalidP:
                    validPort = False
                else: continue
            if validPort is True:
                print("valid port " + port.description)
                self.defaultPort = port.device
                return port.device
                
        return None
    
    def stopAllTasks(self):
        try:
            # stop all timer here
            self.redrawTimer.Stop()
            self.comTimer.Stop()

            self.stopReceivingThread()

            self.logger.debug("all tasks are stopped")
            self.logger = None
        except Exception as e:
            self.logger.warning(e)
    
    def read(self, running, connection):
        self._runReadThread = running

        self.logger.debug("Serial Read Thread started")

        if not connection:
            self.logger.error("No Serial connection given")
            return
        else:
            if not connection.isOpen():
                self.logger.warning("Connection not yet active")
                connection.open()
            else:
                pass

        # create endless reading loop in a seperate thread.
        # kill it by calling stopReadingThread()

        # change this variable to stop this thread
        # https://stackoverflow.com/questions/18018033/how-to-stop-a-looping-thread-in-python
        while self._runReadThread:
            if connection and connection.isOpen():
                # for PySerial v3.0 or later, use property "in_waiting"
                # instead of function inWaiting()
                # https://stackoverflow.com/questions/17553543/pyserial-non-blocking-read-loop

                unixMicros = self.getCurrentTime()
                # unixMicros = self.getUnixMicrosTimestamp()
                line = ""

                # if incoming bytes are waiting to be read from serial input
                # buffer
                if (connection.inWaiting() > 0):
                    # read a '\n' terminated line
                    line = connection.readline()

                # if read thing is not empty
                if line != "":
                    self.logger.debug("Read line: %s" %(line))

                    # create dict of this message
                    messageDict = dict()
                    messageDict["timestamp"] = unixMicros
                    messageDict["message"] = str(line,'utf-8') #bydefault it output byte, like b'echo:Home offset:\n', so we need to assign encoding
                    print(str(line,'utf-8'))
                    # AppendText is not thread safe!
                    # self.txtSerialMonitor.AppendText(line)
                    self.fillSerialConsole(data=messageDict)

                time.sleep(0.1)

    def startReceivingThread(self):
        self.pauseReceivingThread(pause=False)
        self._receivingThread = threading.Thread(
            target=self.read,
            args=(True, self._conn),
            # daemon=True,
            name="ReadingThread")
        self._receivingThread.start()

    def pauseReceivingThread(self, pause=False):
        self.logger.info("Pausing receiving thread: %s" %(pause))
        self._runReadThread = not pause

    def stopReceivingThread(self):
        self.logger.info("Stopping receiving thread now")
        self._runReadThread = False

        if self._receivingThread is not None:
            # wait up to 1 second until thread terminates
            self._receivingThread.join(1)

            del self._receivingThread

    def getReceivingThreadState(self):
        return self._runReadThread

    def getUnixMicrosTimestamp(self):
        # given in seconds, multiply by 1000 to get millis, again times 1000 to get micros
        return int(time.time()*1000*1000)

    def getCurrentTime(self):
        return datetime.datetime.now().strftime("%H:%M:%S:%f")

    def getRuntime(self):
        stopTime = datetime.datetime.now()  # get current time
        theRunTime = stopTime - self.startTime  # time difference aka runtime

        return theRunTime

    def fillSerialConsole(self, data):
        # build message string
        textMessage = "%s \t %s" %(data["timestamp"], data["message"])
        # print(textMessage)
        #self.txtSerialMonitor.AppendText(textMessage)

    def OpenPort(self):

        try:

            thisBaudrate = self.defaultBaudrate
            thisPort =  self.defaultPort

            self._conn = serial.Serial(
                port=thisPort,
                baudrate=int(thisBaudrate),
                # parity=serial.PARITY_ODD,
                # stopbits=serial.STOPBITS_TWO,
                # bytesize=serial.SEVENBITS,
                timeout=0.4,  # IMPORTANT, can be lower or higher
                # inter_byte_timeout=0.1  # Alternative
            )
            self._conn.close()

            print('** Baud Rate: %s \n' %(thisBaudrate))
        except serial.serialutil.SerialException as e:
            print('** An Error Occurred while Opening the Serial Port\n')
            self.logger.warning("Error: %s" %(e))


    def ConnectTarget(self):
        # return if connection is None
        if self._conn == None:
            return

        if self._conn.isOpen():
            self.logger.debug("Port is already open")
        else:
            # connection not yet open
            self.logger.debug("Port is not open, opening now")
            self._conn.open()
            time.sleep(0.1)
            # start the receiving thread
            self.startReceivingThread()

            self.logger.debug("Port is open now, ready to receive")
    def DisconnectTarget(self):
        # return if connection is None
        if self._conn == None:
            return

        if self._conn.isOpen():
            # connection is open
            self.logger.debug("Port is open, closing now")

            if self._receivingThread != None:
                # stop any (may already running) receiving thread
                self.stopReceivingThread()
            self._conn.close()
            #self.stopAllTasks()
            self.logger.debug("Port is closed, ready to open")
        else:
            self.logger.debug("Port is already closed")
    def WriteCommand(self,str):
        strout = str + '\r\n'
        if(self._conn != None):
            self._conn.write(strout.encode() )

    def WriteTest(self):
        while True:
            self.WriteCommand('G28')
            time.sleep(3)
            
    def startWriteThread(self):
        self._writeThread = threading.Thread(
            target=self.WriteTest,
            name="WriteThread")
        self._writeThread.start()


    def stopWriteThread(self):
        self.logger.info("Stopping Writing thread now")
        if self._writeThread is not None:
            # wait up to 1 second until thread terminates
            self._writeThread.join(1)
            del self._writeThread

    def CloseApp(self):
        logger = logging.getLogger(__name__)

        self.stopAllTasks()

        if self._conn and self._conn.isOpen():
            self._conn.close()
            self.logger.debug("Closed serial connection")

        logger.info("... closing app after %s" %self.getRuntime())

ser=SerialMonitor()
print(ser.getArduinoPort())
ser.OpenPort()
ser.ConnectTarget()

#wait for it initialize
time.sleep(10)
#test write and see if we have response, this is used during production
ser.WriteCommand('G28')

# test write thread, this is probably not useful for production
ser.startWriteThread()
time.sleep(30)

# stop write thread
ser.stopWriteThread()

#close port
time.sleep(10)
ser.DisconnectTarget()
ser.CloseApp()
