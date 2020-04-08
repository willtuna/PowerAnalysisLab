# Authors: Colin O'Flynn
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
#=================================================
import logging
import sys
import traceback
import chipwhisperer.capture.scopes._qt as openadc_qt
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererFWLoader import CWLite_Loader, CW1200_Loader
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererFWLoader import FWLoaderConfig
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererFWLoaderGUI import FWLoaderConfigGUI
from chipwhisperer.common.utils.pluginmanager import Plugin
from chipwhisperer.common.utils.parameter import Parameterized, Parameter
from chipwhisperer.common.utils.util import DictType

try:
    import chipwhisperer.capture.scopes.cwhardware.ChipWhispererLite as CWL
except ImportError:
    CWL = None
    logging.error("Could not import ChipWhispererLite\n" + traceback.format_exc())

try:
    import usb
except ImportError:
    usb = None
    logging.error("Could not import USB\n" + traceback.format_exc())


class OpenADCInterface_NAEUSBChip(Parameterized, Plugin):
    _name = "NewAE USB (CWLite/CW1200)"

    def __init__(self, oadcInstance):
        self.ser = None
        self.dev = None
        self.scope = None
        self.last_id = None

        self.getParams().addChildren([
            {'name':"CW Firmware Preferences", 'tip':"Configure ChipWhisperer FW Paths", 'type':"menu", "action":lambda _:self.getFwLoaderConfigGUI().show()}, # Can' use Config... name with MacOS
            {'name':"Download CW Firmware", 'tip':"Download Firmware+FPGA To Hardware", 'type':"menu", "action":lambda _:self.cwFirmwareConfig[self.last_id].loadRequired()},
            {'name':"Serial Number", 'key':'cwsn', 'type':"list", 'values':{"Auto":None}, 'value':"Auto"},
        ])

        if (openadc_qt is None) or (usb is None):
            missingInfo = ""
            if openadc_qt is None:
                missingInfo += "openadc.qt "
            if usb is None:
                missingInfo += " usb"
            raise ImportError("Needed imports for ChipWhisperer missing: %s" % missingInfo)
        else:
            self.cwFirmwareConfig = {
                0xACE2:FWLoaderConfig(CWLite_Loader()),
                0xACE3:FWLoaderConfig(CW1200_Loader())
            }
            self.scope = oadcInstance

    def con(self):
        self.findParam('cwsn').setReadonly(False)
        if self.ser is None:
            self.dev = CWL.CWLiteUSB()
            self.getParams().append(self.dev.getParams())

            try:
                nae_products = [0xACE2, 0xACE3]
                possible_sn = self.dev.get_possible_devices(nae_products)
                if len(possible_sn) > 1:
                    #Update list...
                    snlist = DictType({'Select Device to Connect':None})
                    for d in possible_sn:
                        snlist[str(d.serial_number) + " (" + str(d.product) + ")"] = d.serial_number

                    if self.findParam('cwsn').getValue() not in snlist.values():
                        self.findParam('cwsn').setValue(None)

                    self.findParam('cwsn').setLimits(snlist)
                    sn = self.findParam('cwsn').getValue()
                else:
                    self.findParam('cwsn').setValue(None)
                    self.findParam('cwsn').setLimits({"Auto":None})
                    sn = None
                found_id = self.dev.con(idProduct=nae_products, serial_number=sn)
            except (IOError, ValueError):
                raise Warning('Could not connect to "%s". It may have been disconnected, is in an error state, or is being used by another tool.' % self.getName())

            if found_id != self.last_id:
                logging.info("Detected ChipWhisperer with USB ID %x - switching firmware loader" % found_id)
            self.last_id = found_id

            self.getFWConfig().setInterface(self.dev.fpga)
            try:
                self.getFWConfig().loadRequired()
            except:
                self.dev.dis()
                self.dev.usbdev().close()
                raise
            self.ser = self.dev.usbdev()

        try:
            self.scope.con(self.ser)
            logging.info('OpenADC Found, Connecting')
        except IOError, e:
            exctype, value = sys.exc_info()[:2]
            raise IOError("OpenADC: " + (str(exctype) + str(value)))

        #OK everything worked?
        self.findParam('cwsn').setReadonly(True)

    def dis(self):
        self.findParam('cwsn').setReadonly(False)
        if self.ser is not None:
            self.getFWConfig().setInterface(None)
            self.scope.close()
            self.ser.close()
            self.ser = None
        if self.dev is not None:
            self.dev.dis()
            self.dev = None

    def __del__(self):
        if self.ser is not None:
            self.ser.close()

    def getFWConfig(self):
        try:
            return self.cwFirmwareConfig[self.last_id]
        except KeyError as e:
            return FWLoaderConfig(CWLite_Loader())

    def getFwLoaderConfigGUI(self):
        return FWLoaderConfigGUI(self.getFWConfig(), self.ser is not None)
