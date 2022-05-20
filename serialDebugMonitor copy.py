
import logging
import datetime
import queue

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
        self.availablePorts = list()
        ports = list(port_list.comports())

        self.availablePorts = list()
        for p in ports:
            self.availablePorts.append(p.device)

        self._receivingThread = None
        self._runReadThread = False
        self._conn = None
        self._recievedQueue = queue.Queue()
        self.maxSerialChars = 10*1000



    ##
    ## @brief      Stop all active tasks
    ##
    ## @param      self  The object
    ##
    ## @return     None
    ##
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
    
    ##
    ## @brief      Read the USB port in an endless loop
    ##
    ## @param      self     The object
    ## @param      running  Bool to stay in the while loop
    ##
    ## @return     None
    ##
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
                    # add this message dict to the received queue
                    # self._recievedQueue.put(messageDict)

                    # AppendText is not thread safe!
                    # self.txtSerialMonitor.AppendText(line)
                    self.fillSerialConsole(data=messageDict)

                time.sleep(0.1)

    """
    def getReceiveQueue(self):
        return self._recievedQueue
    """

    ##
    ## @brief      Starts the receiving thread.
    ##
    ## @param      self  The object
    ##
    ## @return     None
    ##
    def startReceivingThread(self):
        self.pauseReceivingThread(pause=False)
        self._receivingThread = threading.Thread(
            target=self.read,
            args=(True, self._conn),
            # daemon=True,
            name="ReadingThread")
        self._receivingThread.start()

    ##
    ## @brief      Pause receiving thread
    ##
    ## @param      self   The object
    ## @param      pause  The pause
    ##
    ## @return     None
    ##
    def pauseReceivingThread(self, pause=False):
        self.logger.info("Pausing receiving thread: %s" %(pause))
        self._runReadThread = not pause

    ##
    ## @brief      Stop the receiving thread
    ##
    ## @param      self  The object
    ##
    ## @return     None
    ##
    def stopReceivingThread(self):
        self.logger.info("Stopping receiving thread now")
        self._runReadThread = False

        if self._receivingThread is not None:
            # wait up to 1 second until thread terminates
            self._receivingThread.join(1)

            del self._receivingThread

    ##
    ## @brief      Gets the receiving thread state.
    ##
    ## @param      self  The object
    ##
    ## @retval     True     Running receiving commands from device
    ## @retval     False    Not receiving commands from device
    ##
    def getReceivingThreadState(self):
        return self._runReadThread

    ##
    ## @brief      Gets the unix timestamp in micros.
    ##
    ## @param      self  The object
    ##
    ## @return     The unix timestamp in micros.
    ##
    def getUnixMicrosTimestamp(self):
        # given in seconds, multiply by 1000 to get millis, again times 1000 to get micros
        return int(time.time()*1000*1000)

    ##
    ## @brief      Gets the current time.
    ##
    ## Format is Hour:Minutes:Seconds:Microseconds
    ##
    ## @param      self  The object
    ##
    ## @return     The timestamp as string.
    ##
    def getCurrentTime(self):
        return datetime.datetime.now().strftime("%H:%M:%S:%f")

    ##
    ## @brief      Return runtime of the app
    ##
    ## @param      self  The object
    ##
    ## @return     The runtime
    ##
    def getRuntime(self):
        stopTime = datetime.datetime.now()  # get current time
        theRunTime = stopTime - self.startTime  # time difference aka runtime

        return theRunTime

    def restorePortSelection(self, portString):
        matchingIndexList = list()

        # search for matching string in available ports, if portString not ""
        if len(portString):
            # search for matches of self.defaultPort in available ports list
            matchingIndexList = [idx for idx, val in enumerate(self.availablePorts) if portString in val]

        # comboBox selection is done by index, -1 is None/empty selection
        matchingIndex = -1

        if len(matchingIndexList):
            # take first match if list contains at least 1 element
            matchingIndex = matchingIndexList[0]
        else:
            pass
            # specify explicit value or use wx constant
            # matchingIndex = wx.NOT_FOUND

            # self.logger.warning("Specified defaultPort is not available for selection, using None/empty")

        # pre-select the port of the port combo box
        self.cmbPorts.SetSelection(matchingIndex)

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
            # connection is open
            self.logger.debug("Port is open, closing now")

            if self._receivingThread != None:
                # stop any (may already running) receiving thread
                self.stopReceivingThread()

            self._conn.close()

            #self.stopAllTasks()

            self.logger.debug("Port is closed, ready to open")
        else:
            # connection not yet open
            self.logger.debug("Port is not open, opening now")

            self._conn.open()

            time.sleep(0.1)

            # start the receiving thread
            self.startReceivingThread()

            self.logger.debug("Port is open now, ready to receive")

    def WriteCommand(self,str):
        strout = str + '\r\n'
        if(self._conn != None):
            self._conn.write(strout.encode() )



    ##
    ## @brief      Quit app and stop all tasks
    ##
    ## @param      self   The object
    ## @param      event  The event
    ##
    ## @return     None
    ##
    def CloseApp(self):
        logger = logging.getLogger(__name__)

        self.stopAllTasks()

        if self._conn and self._conn.isOpen():
            self._conn.close()
            self.logger.debug("Closed serial connection")

        logger.info("... closing app after %s" %self.getRuntime())

        self.Destroy()

ser=SerialMonitor()
ser.OpenPort()
ser.ConnectTarget()
ser.WriteCommand('G28')

