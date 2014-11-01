import sys
import logging
from abc import ABCMeta,abstractmethod
from switchyard.lib.address import IPAddr,EthAddr
from switchyard.lib.textcolor import *

# version test, for sanity
if sys.version_info.major < 3 or sys.version_info.minor < 4:
    with red():
        print("Switchyard requires Python 3.4")
    sys.exit(-1)

class SwitchyException(Exception):
    pass

class Shutdown(Exception):
    pass

class NoPackets(Exception):
    pass

class ScenarioFailure(Exception):
    pass

class PacketFormatter(object):
    __fulldisp = False

    @staticmethod
    def full_display():
        PacketFormatter.__fulldisp = True

    @staticmethod
    def format_pkt(pkt, cls=None):
        '''
        Return a string representation of a packet.  If display_class is a known
        header type, just show the string repr of that header.  Otherwise, dump
        the whole thing.
        '''
        if PacketFormatter.__fulldisp:
            cls = None
            
        # FIXME!!! needs update from POX packet library
        #if cls:
        #    if not pkt.parsed:
        #        raw = pkt.pack()
        #        pkt.parse(raw)
        #    header = pkt.find(cls)
        #    if header is not None:
        #        return str(header)
        return str(pkt)

class Interface(object):
    '''
    Class that models a single logical interface on a network
    device.  An interface has a name, 48-bit Ethernet MAC address,
    and a 32-bit IPv4 address and mask.
    '''
    def __init__(self, name, ethaddr, ipaddr, netmask):
        self.__name = name
        self.ethaddr = ethaddr
        self.ipaddr = ipaddr
        self.netmask = netmask

    @property
    def name(self):
        return self.__name

    @property
    def ethaddr(self):
        return self.__ethaddr

    @ethaddr.setter
    def ethaddr(self, value):
        if isinstance(value, EthAddr):
            self.__ethaddr = value
        elif isinstance(value, str):
            self.__ethaddr = EthAddr(value)
        elif value is None:
            self.__ethaddr = '00:00:00:00:00:00'
        else:
            self.__ethaddr = value

    @property 
    def ipaddr(self):
        return self.__ipaddr

    @ipaddr.setter
    def ipaddr(self, value):
        if isinstance(value, IPAddr):
            self.__ipaddr = value
        elif isinstance(value, str):
            self.__ipaddr = IPAddr(value)
        elif value is None:
            self.__ipaddr = '0.0.0.0'
        else:
            self.__ipaddr = value

    @property 
    def netmask(self):
        return self.__netmask

    @netmask.setter
    def netmask(self, value):
        if isinstance(value, IPAddr):
            self.__netmask = value
        elif isinstance(value, str):
            self.__netmask = IPAddr(value)
        elif value is None:
            self.__netmask = '255.255.255.255'
        else:
            self.__netmask = value

    def __str__(self):
        return "{} mac:{} ip:{}/{}".format(str(self.name), str(self.ethaddr), str(self.ipaddr), str(self.netmask))

def setup_logging(debug):
    '''
    Setup logging format and log level.
    '''
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format="%(asctime)s %(levelname)8s %(message)s", datefmt="%T %Y/%m/%d", level=level)

def log_failure(s):
    '''Convenience function for failure message.'''
    with red():
        logging.fatal("{}".format(s))

def log_debug(s):
    '''Convenience function for debugging message.'''
    logging.debug("{}".format(s))

def log_warn(s):
    '''Convenience function for warning message.'''
    with magenta():
        logging.warn("{}".format(s))

def log_info(s):
    '''Convenience function for info message.'''
    logging.info("{}".format(s))


class LLNetBase(metaclass=ABCMeta):
    '''
    Base class for low-level networking library in Python.
    '''
    def __init__(self, name=None):
        self.devupdown_callback = None
        self.devinfo = {} # dict(str -> Interface)

    def set_devupdown_callback(self, callback):
        '''
        Set the callback function to be invoked when
        an interface goes up or down.  The arguments to the
        callback are: Interface (object representing the interface
        that has changed status), string (either 'up' or 'down').

        (function) -> None
        '''
        self.devupdown_callback = callback

    def interfaces(self):
        '''
        Return a list of interfaces incident on this node/router.
        Each item in the list is an Interface (devname,macaddr,ipaddr,netmask) object.
        '''
        return self.devinfo.values()

    def ports(self):
        '''
        Alias for interfaces() method.
        '''
        return self.interfaces()

    def interface_by_name(self, name):
        '''
        Given a device name, return the corresponding interface object
        '''
        if name in self.devinfo:
            return self.devinfo[name]
        raise SwitchyException("No device named {}".format(name))

    def port_by_name(self, name):
        '''
        Alias for interface_by_name
        '''
        return self.interface_by_name(name)

    def interface_by_ipaddr(self, ipaddr):
        '''
        Given an IP address, return the interface that 'owns' this address
        '''
        ipaddr = IPAddr(ipaddr)
        for devname,iface in self.devinfo.items():
            if iface.ipaddr == ipaddr:
                return iface
        raise SwitchyException("No device has IP address {}".format(ipaddr))

    def port_by_ipaddr(self, ipaddr):
        '''
        Alias for interface_by_ipaddr
        '''
        return self.interface_by_ipaddr(ipaddr)

    def interface_by_macaddr(self, macaddr):
        '''
        Given a MAC address, return the interface that 'owns' this address
        '''
        macaddr = EthAddr(macaddr)
        for devname,iface in self.devinfo.items():
            if iface.ethaddr == macaddr:
                return iface
        raise SwitchyException("No device has MAC address {}".format(macaddr))

    def port_by_macaddr(self, macaddr):
        '''
        Alias for interface_by_macaddr
        '''
        return self.interface_by_macaddr(macaddr)

    @abstractmethod
    def recv_packet(self, timeout=0.0, timestamp=False):
        raise NoPackets()

    @abstractmethod
    def send_packet(self, dev, packet):
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def name(self):
        pass
