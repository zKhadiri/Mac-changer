# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from ServiceReference import ServiceReference
from Components.config import ConfigSubsection, ConfigDirectory, ConfigSelection, getConfigListEntry, config, ConfigYesNo, ConfigLocations,ConfigText,ConfigMAC
from Components.ConfigList import ConfigList, ConfigListScreen
import netifaces,io,os,re
from time import sleep

config.plugins.MacPlugin = ConfigSubsection()

config.plugins.MacPlugin.intf = ConfigSelection(default = "1", choices = [("1",_("eth0"))])
config.plugins.MacPlugin.mac = ConfigText(default='', fixed_size=False)
config.plugins.MacPlugin.new = ConfigText()
cfg = config.plugins.MacPlugin


class Mac(Screen,ConfigListScreen):
    skin="""
        <screen position="center,center" size="500,200" title="MAC CHANGER BY ZIKO" backgroundColor="#31000000" flags="wfNoBorder">
            <widget name="config" position="10,10" size="480,200" zPosition="1" transparent="0" backgroundColor="#31000000" scrollbarMode="showOnDemand" />
        </screen>"""
        
    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self.onChangedEntry = []
        self.list = []
        ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)
        self["myActionMap"] = ActionMap(['InputBoxActions'],
        {   
            "back": self.exit,
            "ok":self.ok,
        }, -1)
        
        self.init()
        
    def init(self):
        self.list = [ getConfigListEntry(_("interface"), cfg.intf) ]
        self.list.append(getConfigListEntry(_("current mac address"), cfg.mac))
        self.list.append(getConfigListEntry(_("new mac address"), cfg.new))
        cfg.mac.value = str(dict(netifaces.ifaddresses('eth0')[netifaces.AF_LINK][0])['addr'].upper())
        with open("/usr/lib/enigma2/python/Plugins/Extensions/Mac_Plugin/mac.txt") as f:
            self.mac_new = f.read()

        cfg.new.value = str(self.mac_new.upper().strip())
        self["config"].list = self.list
        self["config"].setList(self.list)

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()
    
    def ok(self):
        self.session.openWithCallback(self.go, MessageBox, _('Are you sure you want to change current mac address : '+cfg.mac.value), MessageBox.TYPE_YESNO)
    
    def go(self,answer=False):
        if answer:
            if re.match('\w{2}:\w{2}:\w{2}:\w{2}:\w{2}:\w{2}',cfg.new.value):
		cfg.new.save()
                os.system('ifconfig eth0 down')
                sleep(2)
                os.system('ifconfig eth0 down hw ether '+str(cfg.new.value))
                sleep(2)
                os.system('ifconfig eth0 up')
                self.check()
                sleep(2)
                os.system('/etc/init.d/networking restart')
                try:
                    current_ip = str(dict(netifaces.ifaddresses('eth0')[netifaces.AF_INET][0])['addr'])
                except:
                    current_ip = "unknown"
                self.session.open(MessageBox,_("Mac address successfully changed\nNew mac address : "+cfg.new.value+'\nIP : '+current_ip), MessageBox.TYPE_INFO,timeout=10)
                self.close(None)
            else:
                self.session.open(MessageBox,_("Not valide mac address"), MessageBox.TYPE_INFO,timeout=10)
    
    def check(self):
        with open('/etc/network/interfaces', 'r') as file :
            filedata = file.read()
        if "hwaddress ether" in filedata:
            old_mac = re.findall(r'hwaddress ether (\w{2}:\w{2}:\w{2}:\w{2}:\w{2}:\w{2})',filedata)[0]
            filedata = filedata.replace(old_mac, cfg.new.value)
            with open('/etc/network/interfaces', 'w') as file:
                file.write(filedata)
        else:
            inputfile = open('/etc/network/interfaces', 'r').readlines()
            write_file = open('/etc/network/interfaces','w')
            for line in inputfile:
                write_file.write(line)
                if 'iface eth0 inet dhcp' in line or "iface eth0 inet static" in line :
                    new_line = "	hwaddress ether "+cfg.new.value        
                    write_file.write(new_line + "\n") 
            write_file.close()
    
    def exit(self):
        self.close(None)
        
def main(session,**kwargs):
    session.open(Mac)


def Plugins(**kwargs):
	return PluginDescriptor(
			name="MAC",
			description="mac changer by ziko",
			where = PluginDescriptor.WHERE_PLUGINMENU,
			icon="mac.png",
			fnc=main)    
