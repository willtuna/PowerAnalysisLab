"""Contains the test suite for the example scripts found in the software"""

import unittest
import os
import time
import subprocess
import logging
from datetime import datetime

from chipwhisperer.capture.acq_patterns.basic import AcqKeyTextPattern_Basic
import chipwhisperer.tests.tools_for_tests as test_tools
from chipwhisperer.capture.api.programmers import XMEGAProgrammer

import chipwhisperer as cw
from chipwhisperer.tests.tools_for_tests import TESTS_DIR, FIRMWARE_DIR, CAPTURE_SCRIPTS_DIR, \
                                                ANALYZER_SCRIPTS_DIR

# Create test directory if not already there
if not os.path.exists(TESTS_DIR):
    os.makedirs(TESTS_DIR)


class TestTutorialB5BreakingAESStraightForward(unittest.TestCase):
    """Contains test for TutorialB1 SimpleSerial

    NOTE: This test emulates what the user would do in the gui and is
    not the correct way to use the software without the gui (as a python package)
    """

    def setUp(self):
        self.test_name = 'Tutorial_B5_AES_StraightForward'

        now = datetime.now()
        date_string = '-'.join([
            '{:02}'.format(now.year),
            '{:02}'.format(now.month),
            '{:02}'.format(now.day),
            '{:02}'.format(now.hour),
            '{:02}'.format(now.minute),
        ])

        # Create directory tutorial B1 tests if it does not exist
        self.tutorial_directory = os.path.join(TESTS_DIR, self.test_name)
        if not os.path.exists(self.tutorial_directory):
            os.makedirs(self.tutorial_directory)

        # Create log file for the test session
        logfile_name = '_'.join([date_string, self.test_name])
        logfile_name = ''.join([logfile_name, '.log'])
        logfile_path = os.path.join(self.tutorial_directory, logfile_name)
        logging.basicConfig(filename=logfile_path, filemode='w', level=logging.INFO)

        # create project
        project_name ='_'.join([date_string, self.test_name, '.cwp'])
        self.project_save_path = os.path.join(self.tutorial_directory, project_name)
        logging.info('Creating project file: {}'.format(self.project_save_path))
        self.project = cw.createProject(os.path.join(self.project_save_path), overwrite=True)
        logging.info('Finished creating project file')


    def tearDown(self):
        try:
            self.auto_ui.close_capture()
        except Exception as e:
            logging.error(e)
        try:
            self.auto_ui.close_analyzer()
        except Exception as e:
            logging.error(e)

        self.auto_ui.capture.gui.scope.dis()
        self.auto_ui.capture.gui.target.dis()

    def test_TutorialB5(self):
        self.aes_firmware_dir = os.path.join(FIRMWARE_DIR, "simpleserial-aes")

        # Build firmware
        logging.info('Building firmware from make file')
        call = ["make", "--directory", self.aes_firmware_dir, "PLATFORM=CW303"]
        logging.info(call)
        exit_code = subprocess.check_call(call)
        if exit_code == 0:
            logging.info('Finished building firmware')
        else:
            logging.error('Build Failed with exit code {}'.format(exit_code))

        # create capture gui
        self.auto_ui = test_tools.FakeUI()
        self.auto_ui.create_capture()
        capture_gui = self.auto_ui.capture.gui

        # TODO use the created project (currently cause PyQtGraph error)

        # connect scope and target
        logging.info('Executing "connect_cwlite_simpleserial.py"')
        connect_cwlite_simpleserial = os.path.join(CAPTURE_SCRIPTS_DIR, "connect_cwlite_simpleserial.py")
        capture_gui.execute(script_path=connect_cwlite_simpleserial)
        self.auto_ui.updateUI()
        logging.info('Finished executing "connect_cwlite_simpleserial.py"')

        # program the target with the built firmware
        programmer = XMEGAProgrammer()
        programmer.scope = capture_gui.scope
        programmer._logging = None
        programmer.find()
        programmer.erase()
        aes_hex = os.path.join(self.aes_firmware_dir, r"simpleserial-aes-CW303.hex")
        programmer.program(aes_hex, memtype="flash", verify=True)
        programmer.close()

        # Execute the setup script for simple serial aes
        logging.info('Executing "setup_cwlite_xmega_aes.py"')
        setup_cwlite_xmega_aes = os.path.join(CAPTURE_SCRIPTS_DIR, "setup_cwlite_xmega_aes.py")
        capture_gui.execute(script_path=setup_cwlite_xmega_aes)
        self.auto_ui.updateUI()
        logging.info('Finished executing "setup_cwlite_xmega.py"')

        # Create a basic key text pattern
        logging.info('Creating key text pattern')
        ktp = AcqKeyTextPattern_Basic()
        logging.info('Finished creating key text pattern')

        # Capture traces
        logging.info('Capturing traces')
        capture_gui.execute(string='self.api.setNumTraces(60)')
        capture_gui.doCapture(capture_gui.captureM)
        self.auto_ui.updateUI()
        logging.info('Finished capturing traces')

        # Close the capture gui and open the analyzer gui
        logging.info('Closing capture and opening analyzer')
        self.auto_ui.close_capture()
        self.auto_ui.create_analyzer()
        analyzer_gui = self.auto_ui.analyzer.gui
        logging.info('Finished closing capture and opening analyzer')

        # TODO Open the project in the analyzer gui
        #logging.info('Opening project')
        #analyzer_gui.project = self.project
        #logging.info('Finished opening project')

        # Perform the attack
        attack_cpa_script = os.path.join(ANALYZER_SCRIPTS_DIR, "attack_cpa.py")
        logging.info('Executing attack script {}'.format(attack_cpa_script))
        analyzer_gui.execute(script_path=attack_cpa_script)
        self.auto_ui.updateUI()
        logging.info('Finished executing attack script')

        # check if the key is the expected key
        result_subkeys = self.auto_ui.analyzer.gui.results_table.sub_key_row(1)
        result_key = u' '.join(result_subkeys)
        actual_key = ktp.initkey

        logging.info('Actual Key: {}'.format(actual_key))
        logging.info('Result Key: {}'.format(result_key))

        if result_key == actual_key:
            logging.info('Sucess, keys match')
        else:
            logging.error('Keys do not match')
        self.assertEqual(result_key, actual_key)

        # close the analayzer
        self.auto_ui.close_analyzer()


if __name__ == '__main__':
    tutB5_suite = unittest.makeSuite(TestTutorialB5BreakingAESStraightForward)

    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(tutB5_suite)



