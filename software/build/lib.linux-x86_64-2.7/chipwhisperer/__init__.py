from chipwhisperer.capture.api.acquisition_controller import AcquisitionController
from chipwhisperer.capture.acq_patterns.basic import AcqKeyTextPattern_Basic
from chipwhisperer.common.utils.util import updateUI

import os, os.path
from chipwhisperer.common.traces import TraceContainerNative as trace_container_native
from chipwhisperer.common.api import ProjectFormat as project

from chipwhisperer.capture.scopes.OpenADC import OpenADC as cwhardware
from chipwhisperer.capture.targets.SimpleSerial import SimpleSerial as cwtarget
from chipwhisperer.common.api.CWCoreAPI import CWCoreAPI
from chipwhisperer.capture.acq_patterns.basic import AcqKeyTextPattern_Basic as BasicKtp
from chipwhisperer.common.utils.util import cw_bytearray

from chipwhisperer.common.utils.parameter import Parameter
import chipwhisperer.capture.ui.CWCaptureGUI as cwc
import chipwhisperer.analyzer.ui.CWAnalyzerGUI as cwa
from chipwhisperer.common.api.CWCoreAPI import CWCoreAPI
from chipwhisperer.capture.scopes.base import ScopeTemplate
from chipwhisperer.capture.targets._base import TargetTemplate

from functools import wraps

def gui_only(func):
    """Decorator for the functions that can only be used in the gui
    If it is called outside the gui, it will raise UserWarning
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        gui_warning = "This api function is for use inside GUI Python Console"
        try:
            api = CWCoreAPI.getInstance()
            if api is None:
                raise Exception
        except:
            raise UserWarning(gui_warning)
        return func(api, *args, **kwargs)
    return wrapper


def capture_gui():
    """Open the CWCapture GUI, blocking until it's closed.

    Note that opening the GUI does not use any existing scope/target/project objects that were made using the API.

    Known issue: after finishing this function, many API calls don't work from the command line, as ChipWhisperer
    then relies on PyQT for timers and other utilities.
    """
    from chipwhisperer.capture.ui.CWCaptureGUI import main
    main()

def analyzer_gui():
    """Open the Analyzer GUI, blocking until it's closed.
    """
    from chipwhisperer.analyzer.ui.CWAnalyzerGUI import main
    main()

def openProject(filename):
    """Load an existing project from disk.

    Raise an IOError if no such project exists.
    """
    if not os.path.isfile(filename):
        raise IOError("File " + filename + " does not exist or is not a file")
    proj = project.ProjectFormat()
    proj.load(filename)
    return proj

def createProject(filename, overwrite=False):
    """Create a new project with the path <filename>.

    If <overwrite> is False, raise an IOError if this path already exists.
    """
    if os.path.isfile(filename) and (overwrite == False):
        raise IOError("File " + filename + " already exists")

    proj = project.ProjectFormat()
    proj.setFilename(filename)

    return proj


def scope(type = cwhardware):
    """Create a scope object and connect to it.

    This function allows any type of scope to be created. By default, the scope
    is a ChipWhisperer OpenADC object, but this can be set to any valid scope
    class.
    """
    scope = type()
    scope.con()
    return scope

def target(scope, type = cwtarget, **kwargs):
    """Create a target object and connect to it.
    """
    target = type()
    target.con(scope, **kwargs)
    return target

@gui_only
def auxList(api):
    # TODO: this should create a fresh aux list
    # We can already access API one via self.aux_list
    return api.getAuxList()

@gui_only
def captureN(api, scope=None, target=None, project=None, aux_list=None, ktp=None, N=1, seg_size=None):
    """Capture a number of traces, saving power traces and input/output text
    and keys to disk along the way.

    Args:
        scope: A connected scope object. If None, no power trace will be
            recorded - possibly helpful for testing target setups
        target: A connected target object. If None, no target commmands will be
            sent - assumed that aux commands or external boards are controlling
            target
        project: A ChipWhisperer project object. If None, no data will be
            saved - helpful when testing scope settings without saving
        aux_list: An AuxList object with auxiliary functions registered. If
            None, no auxiliary functions are run
        ktp: A key/text input object. Produces pairs of encryption key/input
            text for each capture. Can't be None as these values are required
        N: The number of traces to capture.
        seg_size: The number of traces to record in each segment. The data is
            saved to disk in a number of segments to avoid making one enormous
            data file. If None, a sane default is used.

    To emulate GUI capture:
    >>> cw.captureN(self.scope, self.target, self.project, self.aux_list, self.ktp, 50)
    """
    api.captureM(scope=scope, target=target, project=project, aux_list=aux_list, ktp=ktp, N=N, seg_size=seg_size)

@gui_only
def getLastKey(core_api):
    """Return the last key used in captureN
    """
    key = core_api.getLastKey()
    if key is None:
        return key
    else:
        return cw_bytearray(key)

@gui_only
def getLastTextin(core_api):
    """Return the last input text used in captureN
    """
    lti = core_api.getLastTextin()
    if lti is None:
        return lti
    else:
        return cw_bytearray(lti)

@gui_only
def getLastTextout(core_api):
    """Return the last input text used in captureN
    """
    lto = core_api.getLastTextout()
    if lto is None:
        return lto
    else:
        return cw_bytearray(lto)

@gui_only
def getLastExpected(core_api):
    """Return the last input text used in captureN
    """
    le = core_api.getLastExpected()

    if le is None:
        return le
    else:
        return cw_bytearray(le)


# TODO: decide whether to remove all of this
class gui(object):
    def __init__(self):
        Parameter.usePyQtGraph = True
        self.api = CWCoreAPI()

    def register_scope(self, obj):
        self.api.setScope(obj, addToList=True, blockSignal=True)


    def register_target(self, obj):
        self.api.setTarget(obj, addToList=True, blockSignal=True)

    def register(self, obj):
        #Figure out what we're registering here
        if isinstance(obj, ScopeTemplate):
            self.register_scope(obj)
        elif isinstance(obj, TargetTemplate):
            self.register_target(obj)
        else:
            raise ValueError("Unknown object type %s"%str(obj))

    def capture(self):
        self.app = cwc.makeApplication("Capture")
        self.window = cwc.CWCaptureGUI(self.api)
        self.window.show()
        # Run the main Qt loop
        self.app.exec_()


def acquisition_controller(scope, target=None, writer=None, aux=None, key_text_pattern=None):
    """Not required when running GUI"""
    ac = AcquisitionController(scope=scope, target=target, keyTextPattern=key_text_pattern)
    return ac
