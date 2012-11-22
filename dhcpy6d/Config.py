# encoding: utf8
#
# config
#

import sys 
import ConfigParser
import os.path
import uuid
import time
import datetime
import shlex
import copy
from Helpers import *

# needed for boolean options
BOOLPOOL = {"0":False, "1":True, "no":False, "yes":True, False:False, True:True, "on":True, "off":False}

# whitespace for options with more than one value
WHITESPACE = " ,"

class Config(object):
    """
      general settings  
    """           
    def _check_config(self):
        """
        checks validity of config settings
        """
        print "Checking configuration..."
        #try:
        msg_prefix = "General configuration:"
        # check interface for multicast
        for i in self.INTERFACE:
            if not i.isalnum():
                ErrorExit("%s Interface '%s' must be alphanumeric." % (msg_prefix, self.INTERFACE))
        # check multicast address
        try:
            DecompressIP6(self.MCAST)
        except Exception, err:
            ErrorExit("%s Multicast address '%s' is invalid." % (msg_prefix, err))
        if not self.MCAST.lower().startswith("ff"):    
            ErrorExit("%s Multicast address '%s' is invalid." % (msg_prefix, err))
        
        # check DHCPv6 port    
        if not self.PORT.isdigit():
            ErrorExit("%s Port '%s' is invalid" % (msg_prefix, self.PORT))
        elif not  0 < int(self.PORT) <= 65535:
            ErrorExit("%s Port '%s' is invalid" % (msg_prefix, self.PORT))
        
        # check server's address    
        try:
            DecompressIP6(self.ADDRESS)
        except Exception, err:
            ErrorExit("%s Server address '%s' is invalid." % (msg_prefix, err))
        
        # check server duid    
        if not self.SERVERDUID.isalnum():
            ErrorExit("%s Server DUID '%s' must be alphanumeric." % (msg_prefix, self.SERVERDUID))
        
        # check nameserver to be given to client
        for nameserver in self.NAMESERVER:
            try:
                DecompressIP6(nameserver)
            except Exception, err:
                ErrorExit("%s Name server address '%s' is invalid." % (msg_prefix, err))
        
        # partly check of domain name validity     
        for i in self.DOMAIN.lower():
            if not i in ".-0123456789abcdefghijklmnopqrstuvwxyz":
                ErrorExit("%s Domain name '%s' is invalid." % (msg_prefix, self.DOMAIN))  
        
        # partly check of domain name validity         
        if not self.DOMAIN.lower()[0].isalpha() or \
           not self.DOMAIN.lower()[-1].isalpha():
                ErrorExit("%s Domain name '%s' is invalid." % (msg_prefix, self.DOMAIN)) 
                
        # check if valid lifetime is a number    
        if not self.VALID_LIFETIME.isdigit():
            ErrorExit("%s Valid lifetime '%s' is invalid." % (msg_prefix, self.VALID_LIFETIME))
        
        # check if preferred lifetime is a number    
        if not self.PREFERRED_LIFETIME.isdigit():
            ErrorExit("%s Preferred lifetime '%s' is invalid." % (msg_prefix, self.PREFERRED_LIFETIME))
        
        # check if valid lifetime is longer than preferref lifetime    
        if not int(self.VALID_LIFETIME) > int(self.PREFERRED_LIFETIME):
            ErrorExit("%s Valid lifetime '%s' is shorter than preferred lifetime '%s' and thus invalid." %\
                      (msg_prefix, self.VALID_LIFETIME, self.PREFERRED_LIFETIME) )
            
        # check server preference    
        if not self.SERVER_PREFERENCE.isdigit():
            ErrorExit("%s Server preference '%s' is invalid." % (msg_prefix, self.SERVER_PREFERENCE))               
        elif not  0 <= int(self.SERVER_PREFERENCE) <= 255:
            ErrorExit("Server preference '%s' is invalid" % (self.SERVER_PREFERENCE))
        
        # check information refresh time
        if not self.INFORMATION_REFRESH_TIME.isdigit():
            ErrorExit("%s Information refresh time '%s' is invalid." % (msg_prefix, self.INFORMATION_REFRESH_TIME))
        elif not  0 < int(self.INFORMATION_REFRESH_TIME):
            ErrorExit("%s Information refresh time preference '%s' is pretty short." % (msg_prefix, self.INFORMATION_REFRESH_TIME))
        
        # check validity of configuration source    
        if not self.STORE_CONFIG in ["mysql", "sqlite", "file", False]:
            ErrorExit("%s Unknown config storage type '%s' is invalid." % (msg_prefix, self.STORAGE))
        
        # check which type of storage to use for leases
        if not self.STORE_VOLATILE in ["mysql", "sqlite"]:
            ErrorExit("%s Unknown volatile storage type '%s' is invalid." % (msg_prefix, self.VOLATILE))
        
        # check validity of config file
        if self.STORE_CONFIG == "file":
            if os.path.exists(self.STORE_FILE_CONFIG):
                if not (os.path.isfile(self.STORE_FILE_CONFIG) or \
                   os.path.islink(self.STORE_FILE_CONFIG)):
                    ErrorExit("%s Config file '%s' is no file or link." % (msg_prefix, self.STORE_FILE_CONFIG))
            else:
                ErrorExit("%s Config file '%s' does not exist." % (msg_prefix, self.STORE_FILE_CONFIG))
        
        # check validity of config db sqlite file        
        if self.STORE_CONFIG == "sqlite":
            if os.path.exists(self.STORE_SQLITE_CONFIG):
                if not (os.path.isfile(self.STORE_SQLITE_CONFIG) or \
                   os.path.islink(self.STORE_SQLITE_CONFIG)):
                    ErrorExit("%s SQLite file '%s' is no file or link." % (msg_prefix, self.STORE_SQLITE_CONFIG))
            else:
                ErrorExit("%s SQLite file '%s' does not exist." % (msg_prefix, self.STORE_SQLITE_CONFIG))
                
        # check validity of volatile db sqlite file        
        if self.STORE_VOLATILE == "sqlite":
            if os.path.exists(self.STORE_SQLITE_VOLATILE):
                if not (os.path.isfile(self.STORE_SQLITE_VOLATILE) or \
                   os.path.islink(self.STORE_SQLITE_VOLATILE)):
                    ErrorExit("%s SQLite file '%s' is no file or link." % (msg_prefix, self.STORE_SQLITE_VOLATILE))
            else:
                ErrorExit("%s SQLite file '%s' does not exist." % (msg_prefix, self.STORE_SQLITE_VOLATILE))

        # check logfile's validity    
        if self.LOG:
            if self.LOG_FILE != "":
                if os.path.exists(self.LOG_FILE):
                    if not (os.path.isfile(self.LOG_FILE) or \
                       os.path.islink(self.STORE_FILE_CONFIG)):
                        ErrorExit("%s Logfile '%s' is no file or link." % (msg_prefix, self.LOG_FILE))
                else:
                    ErrorExit("%s Logfile '%s' does not exist." % (msg_prefix, self.LOG_FILE))
            if not self.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                ErrorExit("Log level %s is invalid" % (self.LOG_LEVEL))
                    
        # check authentification information    
        if not self.AUTHENTICATION_INFORMATION.isalnum():
            ErrorExit("%s Authentification information '%s' must be alphanumeric." % (msg_prefix, self.AUTHENTICATION_INFORMATION))
            
        # check validity of identification attributes    
        for i in self.IDENTIFICATION:
            if not i in ["mac", "hostname", "duid"]:
                ErrorExit("%s Identification must consist of 'mac', 'hostname' and/or 'duid'." % (msg_prefix))
        
        # check validity of identification mode
        if not self.IDENTIFICATION_MODE.strip() in ["match_all", "match_some"]:
            ErrorExit("%s Identification mode must be one of 'match_all' or 'macht_some'." % (msg_prefix))
        
        # cruise through classes    
        for c in self.CLASSES:
            for a in self.CLASSES[c].ADDRESSES:
                # test if used addresses are defined
                if not a in self.ADDRESSES:
                    ErrorExit("Class %s: Address type '%s' is not defined." % (c, a))
                # test validity of category
                if not self.ADDRESSES[a].CATEGORY.strip() in ["fixed", "range", "random", "mac", "id"]:
                    ErrorExit(" Address category '%s' is invalid. Category must be one of 'fixed', 'range', 'random' or 'mac'." % (a, self.ADDRESSES[a].CATEGORY))
                # test numberness and length of prefix
                if not self.ADDRESSES[a].PREFIX_LENGTH.strip().isdigit():
                    ErrorExit("Address type '%s': Prefix length '%s' is not a number." % (a, self.ADDRESSES[a].PREFIX_LENGTH.strip()))               
                elif not  0 <= int(self.ADDRESSES[a].PREFIX_LENGTH) <= 128:
                    ErrorExit("Address type '%s': Prefix length '%s' is out of range." % (a, self.ADDRESSES[a].PREFIX_LENGTH.strip())) 
                # test validity of pattern - has its own error output
                self.ADDRESSES[a]._build_prototype()
                # test existence of category specific variable in pattern
                if self.ADDRESSES[a].CATEGORY == "range":
                    if not 0 < self.ADDRESSES[a].PATTERN.count("$range$") < 2:
                        ErrorExit("Address type '%s': Pattern '%s' contains wrong number of '$range$' variables for category 'range'." % (a, self.ADDRESSES[a].PATTERN.strip())) 
                    elif not self.ADDRESSES[a].PATTERN.endswith("$range$"):
                        ErrorExit("Address type '%s': Pattern '%s' must end with '$range$' variable for category 'range'." % (a, self.ADDRESSES[a].PATTERN.strip())) 
                if self.ADDRESSES[a].CATEGORY == "mac":
                    if not 0 < self.ADDRESSES[a].PATTERN.count("$mac$") < 2:
                        ErrorExit("Address type '%s': Pattern '%s' contains wrong number of '$mac$' variables for category 'mac'." % (a, self.ADDRESSES[a].PATTERN.strip())) 
                if self.ADDRESSES[a].CATEGORY == "id":
                    if not 0 < self.ADDRESSES[a].PATTERN.count("$id$") < 2:
                        ErrorExit("Address type '%s': Pattern '%s' contains wrong number of '$id$' variables for category 'id'." % (a, self.ADDRESSES[a].PATTERN.strip())) 
                if self.ADDRESSES[a].CATEGORY == "random":
                    if not 0 < self.ADDRESSES[a].PATTERN.count("$random64$") < 2:
                        ErrorExit("Address type '%s': Pattern '%s' contains wrong number of '$random64$' variables for category 'random'." % (a, self.ADDRESSES[a].PATTERN.strip())) 
                # check ia_type
                
                if not self.ADDRESSES[a].IA_TYPE.strip().lower() in ["na", "ta"]:
                    ErrorExit("Address type '%s': IA type '%s' must be one of 'na' or 'ta'." % (a, self.ADDRESSES[a].IA_TYPE.strip())) 

            # I see no use in checking the filters - if they are usable they
            # will work, otherwise they won't...

        #except:
        #    import traceback
        #    traceback.print_exc(file=sys.stdout)
        #    sys.exit(1)
            
    
    def __init__(self):
        """
            evaluate config file
        """
        # default settings
        # Server cfg.INTERFACE + addresses
        self.INTERFACE = "eth0"
        self.MCAST = "ff02::1:2"
        self.PORT = "547"
        self.ADDRESS = "2001:db8::1"
        # lets make the water turn black... or build a shiny server DUID
        # in case someone will ever debug something here: Wireshark shows
        # year 2042 even if it is 2012 - time itself is OK
        self.SERVERDUID = "00010001%08x%012x" % (time.time(), uuid.getnode())
        self.NAMESERVER = ""
        self.DOMAIN = "domain"

        # IA_NA Options
        # Default preferred lifetime for addresses
        self.PREFERRED_LIFETIME = "5400"
        # Default valid lifetime for addresses
        self.VALID_LIFETIME = "7200"
        # T1 RENEW
        self.T1 = "2700"
        # T2 REBIND
        self.T2 = "4050"
        
        # Server Preference
        self.SERVER_PREFERENCE = "255"

        # SNTP SERVERS Option 31
        self.SNTP_SERVERS = [ self.ADDRESS ]

        # INFORMATION REFRESH TIME option 32 for option 11 (INFORMATION REQUEST)
        # see RFC http://tools.ietf.org/html/rfc4242
        self.INFORMATION_REFRESH_TIME = "6000"    
        
        # config type
        # one of file, mysql, sqlite or none
        self.STORE_CONFIG = "none"
        # one of mysql or sqlite
        self.STORE_VOLATILE = "sqlite"

        # file for client information
        self.STORE_FILE_CONFIG = "clients.conf"
        
        # DB data
        self.STORE_MYSQL_HOST = "localhost"
        self.STORE_MYSQL_DB = "dhcpy6d"
        self.STORE_MYSQL_USER = "user"
        self.STORE_MYSQL_PASSWORD = "password"
        
        self.STORE_SQLITE_CONFIG = "config.sqlite"
        self.STORE_SQLITE_VOLATILE = "volatile.sqlite"

        # DNS Update settings
        self.DNS_UPDATE = False
        self.DNS_UPDATE_NAMESERVER = "::1"
        self.DNS_TTL = 86400
        self.DNS_RNDC_KEY = "rndc-key"
        self.DNS_RNDC_SECRET = "0000000000000000000000000000000000000000000000000000000000000"
        # DNS RFC 4704 client DNS wishes          
        # use client supplied hostname
        self.DNS_USE_CLIENT_HOSTNAME = False
        # ignore client ideas about DNS (if at all, what name to use, self-updating...) 
        self.DNS_IGNORE_CLIENT = True

        # Log ot not
        self.LOG = False
        # Log on console
        self.LOG_CONSOLE = False
        # Logfile
        self.LOG_FILE = ""
        # Log level
        self.LOG_LEVEL = "INFO"
        
        # some 128 bits
        self.AUTHENTICATION_INFORMATION = "00000000000000000000000000000000"
        
        # for debugging 
        self.REALLY_DO_IT = True
        
        # address and class schemes
        self.ADDRESSES = dict()
        self.CLASSES = dict()
        
        self.IDENTIFICATION = "mac"
        self.IDENTIFICATION_MODE = "match_all"
        
        # regexp filters for hostnames etc.
        self.FILTERS = {"mac":[], "duid":[], "hostname":[]}
        
        # define a fallback default class and address scheme
        self.ADDRESSES["default"] = Address(ia_type="na",\
                                                   prefix_length="64",\
                                                   category="mac",\
                                                   pattern="fdef::$mac$",\
                                                   aclass="default",\
                                                   atype="default",\
                                                   prototype="fdef0000000000000000XXXXXXXXXXXX")
        
        self.CLASSES["default"] = Class()
        self.CLASSES["default"].ADDRESSES.append("default")
        
        # define dummy address scheme for fixed addresses
        # pattern and prototype are not really needed as this
        # addresses are fixed
        self.ADDRESSES["fixed"] = Address(ia_type="na",\
                                                   prefix_length="64",\
                                                   category="fixed",\
                                                   pattern="fdef0000000000000000000000000001",\
                                                   aclass="default",\
                                                   atype="fixed",
                                                   prototype="fdef0000000000000000000000000000")              
        
        # config file from command line
        if len(sys.argv) == 1:
            configfile = "dhcpy6d.conf"
        else:
            configfile = sys.argv[1]
            
        if os.path.exists(configfile):
            if not (os.path.isfile(configfile) or \
               os.path.islink(configfile)):
                ErrorExit("Configuration file '%s' is no file or link." % (configfile))
        else:
            ErrorExit("Configuration file '%s' does not exist." % (configfile))

        # instantiate Configparser 
        config = ConfigParser.ConfigParser()
        config.read(configfile)           
        
        # whyever sections classes get overwritten sometimes and so some configs had been missing
        # so create classes and addresses here
        for section in config.sections():
            if section.startswith("class_"):
                self.CLASSES[section.split("class_")[1]] = Class(name=section.split("class_")[1].strip())
            if section.startswith("address_"):
                self.ADDRESSES[section.split("address_")[1].strip()] = Address()
        
        for section in config.sections():
            # go through all items
            for item in config.items(section):
                if section.upper() == "DHCPY6D":
                    # ConfigParser eems to be not case sensitive so settings get normalized
                    object.__setattr__(self, item[0].upper(), str(item[1]).strip())
                else:
                    # global address schemes
                    if section.startswith("address_"):
                        self.ADDRESSES[section.split("address_")[1]].__setattr__(item[0].upper(), str(item[1]).strip())   
                                                            
                    # global classes with their addresses
                    elif section.startswith("class_"):
                        if item[0].upper() == "ADDRESSES":
                            # strip whitespace and separators of addresses
                            lex = shlex.shlex(item[1])
                            lex.whitespace = WHITESPACE
                            lex.wordchars += ":."
                            for address in lex:
                                if len(address) > 0:
                                    self.CLASSES[section.split("class_")[1]].ADDRESSES.append(address) 
                        else:
                            self.CLASSES[section.split("class_")[1]].__setattr__(item[0].upper(), str(item[1]).strip())

        # finetuning
        self.IDENTIFICATION = ListifyOption(self.IDENTIFICATION)

        # get interfaces as list
        self.INTERFACE = ListifyOption(self.INTERFACE)
        
        # create default classes for each interface - if not defined
        # derive from default "default" class
        for i in self.INTERFACE:
            if not "default_" + i in self.CLASSES:
                self.CLASSES["default_" + i] = copy.copy(self.CLASSES["default"])
                self.CLASSES["default_" + i].NAME = "default_" + i
                self.CLASSES["default_" + i].INTERFACE = i
        
        # lower storage
        self.STORE_CONFIG = self.STORE_CONFIG.lower()
        self.STORE_VOLATILE = self.STORE_VOLATILE.lower()
    
        # boolize none-config-store
        if self.STORE_CONFIG == "none":
            self.STORE_CONFIG = False    
       
        # get nameservers as list
        if len(self.NAMESERVER) > 0:
            self.NAMESERVER = ListifyOption(self.NAMESERVER)
        
        # convert to boolean value
        self.DNS_UPDATE = BOOLPOOL[self.DNS_UPDATE]
        self.DNS_USE_CLIENT_HOSTNAME = BOOLPOOL[self.DNS_USE_CLIENT_HOSTNAME]
        self.DNS_IGNORE_CLIENT = BOOLPOOL[self.DNS_IGNORE_CLIENT]
        self.REALLY_DO_IT = BOOLPOOL[self.REALLY_DO_IT]
        self.LOG = BOOLPOOL[self.LOG]
        self.LOG_CONSOLE = BOOLPOOL[self.LOG_CONSOLE]
        self.LOG_LEVEL = self.LOG_LEVEL.upper()
        
        # index of classes which add some identification rules etc.
        
        for c in self.CLASSES.values():
            if c.FILTER_MAC != "": self.FILTERS["mac"].append(c)
            if c.FILTER_DUID != "": self.FILTERS["duid"].append(c)
            if c.FILTER_HOSTNAME != "": self.FILTERS["hostname"].append(c)
            if c.NAMESERVER != "": c.NAMESERVER = ListifyOption(c.NAMESERVER)
            if c.INTERFACE != "":
                c.INTERFACE = ListifyOption(c.INTERFACE)
            else:
                # use general setting if none specified
                c.INTERFACE = self.INTERFACE
            
            # use default T1 and T2 if not defined
            if c.T1 == 0: c.T1 = self.T1
            if c.T2 == 0: c.T2 = self.T2

        # set type properties for addresses
        for a in self.ADDRESSES:
            # name for address, important for leases db
            self.ADDRESSES[a].TYPE = a
            if self.ADDRESSES[a].VALID_LIFETIME == 0: self.ADDRESSES[a].VALID_LIFETIME = self.VALID_LIFETIME
            if self.ADDRESSES[a].PREFERRED_LIFETIME == 0: self.ADDRESSES[a].PREFERRED_LIFETIME = self.PREFERRED_LIFETIME
            # normalize ranges
            self.ADDRESSES[a].RANGE = self.ADDRESSES[a].RANGE.lower()
            # add prototype for later fast validity comparison of rebinding leases
            # also use as proof of validity of address patterns
            self.ADDRESSES[a]._build_prototype()
            # convert boolean string to boolean value
            self.ADDRESSES[a].DNS_UPDATE = BOOLPOOL[self.ADDRESSES[a].DNS_UPDATE]
            if self.ADDRESSES[a].DNS_ZONE == "": self.ADDRESSES[a].DNS_ZONE = self.DOMAIN
            if self.ADDRESSES[a].DNS_TTL == "0": self.ADDRESSES[a].DNS_TTL = self.DNS_TTL
        
        # check config
        self._check_config()
                   
            
class Address(object):
    """
    class for address definition, used for config and clients
    """
    def __init__(self, address=None,\
                 ia_type="na",\
                 prefix_length="64",\
                 category="random",\
                 pattern="2001:db8::$random64$",\
                 preferred_lifetime=0,\
                 valid_lifetime=0,\
                 atype="default",\
                 aclass="default",\
                 prototype="",\
                 range="",\
                 dns_update=False,\
                 dns_zone="",\
                 dns_rev_zone="0.8.b.d.1.0.0.2.ip6.arpa",\
                 dns_ttl = "0",\
                 dns_use_client_fqdn = False,\
                 valid = True):
        self.PREFIX_LENGTH = prefix_length
        self.CATEGORY = category
        self.PATTERN = pattern
        self.IA_TYPE = ia_type
        self.PREFERRED_LIFETIME = preferred_lifetime
        self.VALID_LIFETIME = valid_lifetime
        self.ADDRESS = address
        self.RANGE = range.lower()
        # because "class" is a python keyword we use "aclass" here
        self.CLASS = aclass
        # same with type
        self.TYPE = atype
        # a prototypical address to be compared with leases given by
        # clients - if prototype and lease address kind of match
        # give back the lease as valid
        self.PROTOTYPE = prototype
        # flag for updating address in DNS or not
        self.DNS_UPDATE = dns_update
        # DNS zone data
        self.DNS_ZONE = dns_zone.lower()
        self.DNS_REV_ZONE = dns_rev_zone.lower()
        self.DNS_TTL = dns_ttl
        # flag invalid addresses as invalid, valid ones as valid
        self.VALID = valid
        
        
    def _build_prototype(self):
        """
        build prototype of pattern for later comparison with leases
        """
        a = self.PATTERN
        #a = a.replace("$prefix$", self.PREFIX)
        
        # check different client address categories - to be extended!
        if self.CATEGORY in ["mac", "id", "range", "random"]:
            if self.CATEGORY == "mac":
                a = a.replace("$mac$", "XXXX:XXXX:XXXX")
            elif self.CATEGORY == "id":
                a = a.replace("$id$", "XXXX")
            elif self.CATEGORY == "random":
                a = a.replace("$random64$", "XXXX:XXXX:XXXX:XXXX")
            elif self.CATEGORY == "range":
                a = a.replace("$range$", "XXXX")
            try:
                # build complete "address" and ignore all the Xs (strict=False)
                a = DecompressIP6(a, strict=False)
            except:
                #print "Address", self.TYPE + ": address pattern", self.PATTERN, "is not valid!"
                ErrorExit("Address type '%s' address pattern '%s' is not valid." % (self.TYPE, self.PATTERN))
            
        self.PROTOTYPE = a
        
    
    def matches_prototype(self, address):
        """
        test if given address matches prototype and therefore this address' DNS zone
        information might be used
        only used for address types, not client instances
        """
        match = False
        # compare all chars of address and prototype, if they do match or
        # prototype has placeholder X return finally True, otherwise stop
        # at the first difference and give back False
        for i in range(32): 
            if  self.PROTOTYPE[i] == address[i] or self.PROTOTYPE[i] == "X":
                match = True
            else:
                match = False
                break
        return match
        
            
class Class(object):
    """
    class for class definition
    """
    def __init__(self, name=""):
        self.NAME = name
        self.ADDRESSES = list()
        self.NAMESERVER = ""
        self.FILTER_MAC = ""
        self.FILTER_HOSTNAME = ""
        self.FILTER_DUID = ""
        self.IDENTIFICATION_MODE = "match_all"
        # RENEW time
        self.T1 = 0
        # REBIND time
        self.T2 = 0
        # at which interface this class of clients is served
        self.INTERFACE = ""