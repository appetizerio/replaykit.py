#
# Copyright 2014-2016 Appetizer.io (https://www.appetizer.io)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import os
import subprocess


class RunningTaskControl(object):
    def __init__(self, p):
        self.p = p

    def stop(self):
        """ Signal the task to stop gracefully. Wait until it stops and return its process return code """
        self.p.communicate('please quit\n')
        return self.p.wait()

    def is_finished(self):
        """ Return true if the task is finished """
        return self.p.poll() is not None

    def kill(self):
        """ Forcefully terminate the task """
        self.p.terminate()

    def wait(self):
        """ Wait until the task is done and return its process return code """
        return self.p.wait()


class ADBCommands(object):
    def __init__(self, appetizer):
        self.appetizer = appetizer

    def check_server(self):
        """ Check the state of local ADB server, return a JSON representing its state

        :return: A JSON object. For example: [{"host": "localhost", "version": 36, "port": 5037, "online": true}]
        host is the hostname of the ADB server:
        port is the POSIX port of the ADB server, default to 5037;
        version is the version code of the ADB program (xx in 1.0.xx);
        online indicates if the ADB server can be communicated with;
        """
        return json.loads(self.appetizer.check_output(["adb", "check-server"]))

    def start_server(self):
        """ Start the local ADB server using the adb tool from the Android SDK """
        self.appetizer.call(["adb", "check-server"])

    def kill_server(self):
        """ Kill the local ADB server using the adb tool from the Android SDK """
        self.appetizer.call(["adb", "kill-server"])

    def detect_adb(self):
        """ Detect the path to the adb tool from the Android SDK

        :return: A JSON object. For example: {'adb': '/home/myuser/Android/Sdk/platform-tools/adb'}

        Note that the path could be a unicode string.
        The default installation paths for different OSes are:
        Windows: C:\Users\<User Name>\AppData\Local\Android\sdk\platform-tools\
        Linux: /home/<User Name>/Android/Sdk/platform-tools/adb
        """
        return json.loads(self.appetizer.check_output(["adb", "detectadb"]))


class TraceCommands(object):
    def __init__(self, appetizer):
        self.appetizer = appetizer

    def get_info(self, trace_file):
        """ Get the information about a touchscreen event trace

        :param trace_file: the path to the trace file
        :return: A JSON object. For example:
        {'description': '', 'contacts': 0, 'height': 1920, 'records': 0, 'length': 0.0, 'valid': True, 'width': 1200}
        description is an arbitrary string provided when recording;
        contacts is the maximum number of fingers/tools encountering in the trace;
        height is the pixel height of the recording device screen;
        height is the pixel width of the recording device screen;
        length is the time duration of the trace, in seconds, as a float number;
        valid is a boolean indicating if the given trace is valid;
        records is the number of events recorded in the trace.
        """
        if not os.path.isfile(trace_file):
            return None
        return json.loads(self.appetizer.check_output(["trace", "info", trace_file]))

    def record(self, trace_file, device):
        """ Record a touchscreen event trace from a given device

        :param trace_file: the path to the trace file
        :param device: the device serial number
        :return: a task control object representing the running recording task
        """
        recorder = self.appetizer.run(['trace', 'record', trace_file, '-d', device],
                                    stdin=subprocess.PIPE)
        return RunningTaskControl(recorder)

    def replay(self, trace_file, devices):
        """ Replay a touchscreen event trace to multiple devices

        :param trace_file: the path to the trace file
        :param devices: a list of device serial numbers
        :return: a task control object representing the running replaying task
        """
        replayer = self.appetizer.run(['trace', 'replay', trace_file, ','.join(devices)],
                                    stdin=subprocess.PIPE)
        return RunningTaskControl(replayer)


class DevicesCommands(object):
    def __init__(self, appetizer):
        self.appetizer = appetizer

    def list(self):
        """ List all the devices and their details by communicating with the ADB server

        :return: A JSON array, one per device
        [
          {'screenwidth': 1200, 'uid': 'xxx', u'serialno': 'xxx', 'brand': 'google', 'name': 'razor',
           'screenheight': 1920, 'heapsize': '512m', 'device': 'flo', 'model': 'Nexus 7', 'sdk': '19',
           'os': '4.4.4', 'manufacturer': u'asus'}
        ]
        serialno is the ADB device serial number;
        uid is currently the same as serialno;
        height and width are the pixel dimension of the device screen, object from dumpsys;
        model is the prop ro.product.model;
        name is the prop ro.product.name;
        device is the prop ro.product.device;
        os is the prop ro.build.version.release;
        brand is the prop ro.product.brand;
        manufacturer is the prop ro.product.manufacturer;
        heapsize is the prop dalvik.vm.heapsize;
        sdk is the prop ro.build.version.sdk.
        """
        return json.loads(self.appetizer.check_output(['devices', 'list']))

    def mirror(self, master, slaves):
        """ Synchronize the touchscreen input events from one device (master) to many (slaves), in real-time

        :param master: the serial number of the master device
        :param slaves: a list of serial numbers for slaves
        :return: a task control object representing the running mirroring task
        """
        task = self.appetizer.run(['devices', 'mirror', master, ','.join(slaves)],
                                  stdin=subprocess.PIPE)
        return RunningTaskControl(task)

    def control(self, devices, command, args=None):
        """ Control multiple devices to perform the same operation. Possible commands:

        * reboot              Reboot multiple devices
        * shell               Run a shell command on multiple devices
            - shell_command argument required
            - returns a JSON object showing the shell command result per device
              For example: {"<device_serialno>": "<shell_command_output>", ...}
        * install             Install an apk to multiple devices
            - apk argument (path to the apk file) required
        * uninstall           Uninstall an app (package name) from multiple devices
            - pkg (package name) required
        * launch              Launch an app (based on package name and activity name)
            - pkg (package name) and activity (activity class name) required
        * launch_pkg          Launch the default activity of an app (given package name)
            - pkg (package name) required
        * force_stop          Force-stop an app, not graceful kill
            - pkg (package name) required
        * launch_service      Launch a service (based on package name and service class name)
            - pkg (package name) and service (service class name) required
        * stop_service        Stop a service (based on package name and service class name)
            - pkg (package name) and service (service class name) required
        * kill_all            Kill all background apps

        :param devices: a list of serial numbers for devices
        :param command: the control command
        :param args: the arguments for the control command
        :return: a string, command-specific

        """
        serialnos = ','.join(devices)
        args = args or []
        return self.appetizer.check_output(['devices', 'control', serialnos, command] + args)

    def screenshot(self, save_to, device):
        """ Take a screenshot from a device and save to the local machine

        :param save_to: the path to save the screenshot file (JPG)
        :param device: the serial number of the target device
        """
        self.appetizer.call(['devices', 'screenshot', save_to, '--device', device])


class PlanCommands(object):
    def __init__(self, appetizer):
        self.appetizer = appetizer

    def run(self, plan_file, result_folder, devices, report_url=None):
        """ Run a test plan on multiple devices, store the test result to a folder and optionally report the progress
         via WebSocket

        :param plan_file: the path to the plan file
        :param result_folder: the path to the result folder
        :param devices: a list of serial numbers for test devices
        :param report_url: the WebSocket URL to report real-time progress
        :return: a task control object representing the running test runner
        """
        extra_params = ['--report-url', report_url] if report_url is not None else []
        task = self.appetizer.run(['plan', 'run', plan_file, result_folder, ','.join(devices)] + extra_params,
                                  stdin=subprocess.PIPE)
        return RunningTaskControl(task)


class Appetizer(object):
    COMPAT_LEVEL = 1  # the required compatibility level of the toolkit

    def __init__(self, toolkit):
        self.adb = ADBCommands(self)
        self.devices = DevicesCommands(self)
        self.trace = TraceCommands(self)
        self.plan = PlanCommands(self)
        if type(toolkit) is list:
            self.program = toolkit  # a shell command sequence, e.g. python script.py
        else:
            self.program = [toolkit]  # single executable as program
        self.check_version(Appetizer.COMPAT_LEVEL)

    def check_version(self, required_level):
        v = json.loads(self.check_output(['version']))
        if 'compat' not in v or v['compat'] != required_level:
            raise RuntimeError("Appetizer toolkit is not compatible with the SDK")

    def call(self, args):
        subprocess.call(self.program + args)

    def check_output(self, args):
        return subprocess.check_output(self.program + args)

    def run(self, args, stdin=None, stdout=None, stderr=None):
        return subprocess.Popen(self.program + args, stdin=stdin, stdout=stdout, stderr=stderr)
