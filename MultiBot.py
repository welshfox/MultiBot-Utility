import os
import time
import subprocess
import ConfigParser
from shutil import copyfile

class multiBot:
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read("MultiBotConfig.ini")
        
        self.debugMode = None
        self.loopCounter = None
        self.restartTimer = None
        self.restartEnabled = None
        self.restartMinutes = None
        self.startingLatitude = None
        self.startingLongitude = None
        
        self.bots = []
        self.scans = []
        self.accounts = []
        self.selectedBot = None
        self.currentAccount = None
        
    def main(self):
        print "\n\n[Welshfox's MultiBot Utility]\n"
        self.parseConfig()
        if self.debugMode == False:
            self.selectBot()
            if not self.doesLoginShareConfig(): 
                self.setupCoordInfo()
                time.sleep(0.5)
            if self.restartEnabled:
                self.loopCounter = 1
                while True:
                    print "\n======================================================"
                    print "Selected Bot: " + self.configSectionMap(self.bots[self.selectedBot])['name']
                    print "Scan Loop Count: " + str(self.loopCounter) + "   Accounts Running: " + str(len(self.accounts))
                    print "======================================================\n"
                    self.scans = []
                    self.currentAccount = 0
                    for account in self.accounts:
                        ready = False
                        while not ready: 
                            ready = self.setupAccountInfo()
                            time.sleep(0.5)
                        time.sleep(0.5)
                        self.startScan()
                        if account != self.accounts[-1]:
                            print "Waiting for new scan to finish using config file... Be patient."
                            time.sleep(0.5)
                            self.currentAccount += 1
                    self.restartTimer = time.time()
                    print "Scan(s) were started with auto-restart enabled. Minutes: " + str(self.restartMinutes)
                    while not self.restartReady(): time.sleep(15)
                    print "Stopping all scan(s) and restarting."
                    self.stopScans()
                    self.loopCounter += 1
            else: 
                print "\n======================================================"
                print "Starting one time scan(s). Restart disabled in config."
                print "Selected Bot: " + self.configSectionMap(self.bots[self.selectedBot])['name'] + " Accounts Running: " + str(len(self.accounts))
                print "======================================================\n"
                self.currentAccount = 0
                for account in self.accounts:
                    ready = False
                    while not ready: 
                        ready = self.setupAccountInfo()
                        time.sleep(0.5)
                    time.sleep(0.5)
                    self.startScan()
                    if account != self.accounts[-1]:
                        print "Waiting for new scan to finish using config file... Be patient."
                        time.sleep(0.5)
                        self.currentAccount += 1
                print "\n\nPress Enter to exit..." 
                raw_input() 
        else: 
            print "\nThese are the config settings that the utility sees.\n"
            self.debugPrint()
            print "\n\nPress Enter to exit..." 
            raw_input()
    
    ####################Config Handling###################
    def parseConfig(self):
        self.debugMode = self.configSectionMap("MultiSettings")['debugconfig']
        self.restartEnabled = self.configSectionMap("MultiSettings")['restartenabled']
        self.restartMinutes = self.configSectionMap("MultiSettings")['restarttimer']
        self.startingLatitude = self.configSectionMap("MultiSettings")['startinglatitude']
        self.startingLongitude = self.configSectionMap("MultiSettings")['startinglongitude']
        self.identifyAccounts()
        self.identifyBots()
    
    def configSectionMap(self, section):
        dict = {}
        options = self.config.options(section)
        for option in options:
            try:
                dict[option] = self.config.get(section, option)
                if dict[option] == -1: raise SystemExit("Missing: %s; Please fix config file." % option)
                elif dict[option].upper() == "TRUE": dict[option] = True
                elif dict[option].upper() == "FALSE": dict[option] = False
            except:
                raise SystemExit("Missing: %s; Please fix config file." % option)
        return dict
        
    def identifyAccounts(self):
        sections = self.config.sections()
        for section in sections:
            if "Account_" in section: 
                self.accounts.append(section)
        
    def identifyBots(self):
        sections = self.config.sections()
        for section in sections:
            if "BotType_" in section: 
                self.bots.append(section)
    ######################################################
        
    ######################Bot Handling####################
    def selectBot(self):
        botList = ""
        botCounter = 0
        for bot in self.bots: 
            botList += "[%s]:%s " % (botCounter, self.configSectionMap(bot)['name'])
            botCounter += 1
        print "BOTS: " + botList
        self.selectedBot = input('Choose a bot: ')
        
    def restartReady(self):
        if time.time() - self.restartTimer >= 60 * int(self.restartMinutes): return True
        else: return False
    ######################################################
        
    ###################Process Handling###################
    def startScan(self):
        print "Starting scan for " + self.accounts[self.currentAccount]
        filePath = None
        for root, dirs_list, files_list in os.walk(os.getcwd()):
            for file_name in files_list:
                if file_name == self.configSectionMap(self.bots[self.selectedBot])['botlaunchername']:
                    filePath = os.path.join(root, file_name)
                    setroot = root
                    break
        if filePath != None:
            SW_MINIMIZE = 6
            info = subprocess.STARTUPINFO()
            info.dwFlags = subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = SW_MINIMIZE
            cmd = 'start /MIN ' + filePath
            self.scans.append(subprocess.Popen(filePath, startupinfo=info, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=setroot))
        else: raise SystemExit("Could not locate specified bot launcher. Check Config")
        
    def stopScans(self):
        time.sleep(0.5)
        FNULL = open(os.devnull, 'w')
        for i in range (0, len(self.accounts)):
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.scans[i].pid)], stdout=FNULL)
    ######################################################
    
    ##################Config Manipulation#################
    def doesLoginShareConfig(self):
        user = self.configSectionMap(self.bots[self.selectedBot])['userinfoconfig']
        coord = self.configSectionMap(self.bots[self.selectedBot])['coordinfoconfig']
        if user == coord: return True
        else: return False
    
    def setupCoordInfo(self):
        print "Setting coordinate config for single instance of MultiBot."
        configFilePath = None
        tempConfigPath = None
        configName = self.configSectionMap(self.bots[self.selectedBot])['coordinfoconfig']
        templateName = self.getTemplateName(configName)
        for root, dirs_list, files_list in os.walk(os.getcwd()):
            for file_name in files_list:
                if file_name == configName:
                    configFilePath = os.path.join(root, file_name)
                elif file_name == templateName:
                    tempConfigPath = os.path.join(root, file_name)
        if configFilePath == None: 
            botName = self.configSectionMap(self.bots[self.selectedBot])['name']
            raise SystemExit("Coordinate config file could not be located. SelectedBot: %s Config: %s" % (botName, configName))
        if tempConfigPath == None:
            self.createTemplate(configName, configFilePath, templateName)
        else:
            with open(configFilePath, "wt") as fout:
                with open(tempConfigPath, "rt") as fin:
                    for line in fin:
                        outline = line.replace('MULTIBOTLATITUDE', self.startingLatitude)
                        outline = outline.replace('MULTIBOTLONGITUDE', self.startingLongitude)
                        fout.write(outline)
                    fin.close()
                fout.close()

    def setupAccountInfo(self):
        print "Setting configs for " + self.accounts[self.currentAccount]
        configFilePath = None
        tempConfigPath = None
        configName = self.configSectionMap(self.bots[self.selectedBot])['userinfoconfig']
        templateName = self.getTemplateName(configName)
        for root, dirs_list, files_list in os.walk(os.getcwd()):
            for file_name in files_list:
                if file_name == configName:
                    configFilePath = os.path.join(root, file_name)
                elif file_name == templateName:
                    tempConfigPath = os.path.join(root, file_name)
        if configFilePath == None: 
            botName = self.configSectionMap(self.bots[self.selectedBot])['name']
            raise SystemExit("Account config file could not be located. SelectedBot: %s Config: %s" % (botName, configName))
        if tempConfigPath == None:
            tempConfigPath = self.createTemplate(configName, configFilePath, templateName)
        type = self.configSectionMap(self.accounts[self.currentAccount])['type']
        try:
            with open(configFilePath, "wt") as fout:
                with open(tempConfigPath, "rt") as fin:
                    for line in fin:
                        outline = line.replace('MULTIBOTACCOUNTTYPE', type)
                        if self.doesLoginShareConfig():
                            outline = outline.replace('MULTIBOTLATITUDE', self.startingLatitude)
                            outline = outline.replace('MULTIBOTLONGITUDE', self.startingLongitude)
                        if type == "Google":
                            outline = outline.replace('MULTIBOTGOOGLEUSERNAME', self.configSectionMap(self.accounts[self.currentAccount])['login'])
                            outline = outline.replace('MULTIBOTGOOGLEPASSWORD', self.configSectionMap(self.accounts[self.currentAccount])['pass'])
                        else:
                            outline = outline.replace('MULTIBOTPTCUSERNAME', self.configSectionMap(self.accounts[self.currentAccount])['login'])
                            outline = outline.replace('MULTIBOTPTCPASSWORD', self.configSectionMap(self.accounts[self.currentAccount])['pass'])
                        outline = outline.replace('MULTIBOTSHAREDUSERNAME', self.configSectionMap(self.accounts[self.currentAccount])['login'])
                        outline = outline.replace('MULTIBOTSHAREDPASSWORD', self.configSectionMap(self.accounts[self.currentAccount])['pass'])
                        fout.write(outline)
                    fin.close()
                fout.close()
            return True
        except IOError as ioex:
            return False
    def getTemplateName(self, filename):
        splitname = os.path.basename(filename).split('.')
        if len(splitname) <= 1: raise SystemExit("Make sure you put the file extensions in the config file settings.")
        else:
            templatename = ""
            for i in range (0, len(splitname)-1):
                templatename += splitname[i] + "."
            templatename += "_MBUTemplate." + splitname[-1]
            return templatename
            
    def createTemplate(self, name, path, templateName):
        newpath = path.replace(name, "")
        newpath += templateName
        copyfile(path, newpath)
        time.sleep(0.5)
        return newpath
    ######################################################
    
    def debugPrint(self):
        print "[MultiBot Settings]"
        print " Debug Config Enabled: " + str(self.debugMode)
        print " Restart Enabled: " + str(self.restartEnabled)
        print " Restart Timer (Minutes): " + self.restartMinutes
        print " Starting Latitude: " + self.startingLatitude
        print " Starting Longitude: " + self.startingLongitude
        print ""
        print "[Account Settings]"
        for account in self.accounts: 
            print " Account: " + account
            print " -Type: " + self.configSectionMap(account)['type']
            print " -Login: " + self.configSectionMap(account)['login']
            print " -Pass: " + self.configSectionMap(account)['pass']
        print ""
        print "[Bot Settings]"
        for bot in self.bots: 
            print " Bot: " + str(bot)
            print " -Name: " + self.configSectionMap(bot)['name']
            print " -Dir Path: " + self.configSectionMap(bot)['botfoldername']
            print " -Launch Path: " + self.configSectionMap(bot)['botlaunchername']
            print " -User Config: " + self.configSectionMap(bot)['userinfoconfig']
            print " -Coords Config: " + self.configSectionMap(bot)['coordinfoconfig']
            
if __name__ == '__main__':
    manager = multiBot()
    manager.main()