# Copyright (C) 2012 Claudio "nex" Guarnieri (@botherder)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from lib.cuckoo.common.abstracts import Signature

class VBoxDetectACPI(Signature):
    name = "antivm_vbox_acpi"
    description = "Detects VirtualBox using ACPI tricks"
    severity = 3
    categories = ["anti-vm"]
    authors = ["nex"]
    minimum = "1.0"
    evented = True

    def __init__(self, *args, **kwargs):
        Signature.__init__(self, *args, **kwargs)
        self.lastprocess = None

    def event_apicall(self, call, process):
        if process != self.lastprocess:
            self.opened = False
            self.handle = ""
            self.lastprocess = process

        # First I check if the malware opens the releavant registry key.
        if call["api"].startswith("RegOpenKeyEx"):
            # Store the number of arguments matched.
            args_matched = 0
            # Store the handle used to open the key.
            self.handle = ""
            for argument in call["arguments"]:
                # Check if the registry is HKEY_LOCAL_MACHINE.
                if argument["name"] == "Registry" and argument["value"] == "0x80000002":
                    args_matched += 1
                # Check if the subkey opened is the correct one.
                elif argument["name"] == "SubKey" and argument["value"][:14].upper() == "HARDWARE\\ACPI\\":
                    # Since it could appear under different paths, check for all of them.
                    if argument["value"][14:18] in ["DSDT", "FADT", "RSDT"]:
                        if argument["value"][18:] == "\\VBOX__":
                            return True
                        else:
                            args_matched += 1
                # Store the generated handle.
                elif argument["name"] == "Handle":
                    self.handle = argument["value"]
            
            # If both arguments are matched, I consider the key to be successfully opened.
            if args_matched == 2:
                self.opened = True
        # Now I check if the malware verified the value of the key.
        elif call["api"].startswith("RegEnumKeyEx"):
            # Verify if the key was actually opened.
            if not self.opened:
                return

            # Verify the arguments.
            args_matched = 0
            for argument in call["arguments"]:
                if argument["name"] == "Handle" and argument["value"] == self.handle:
                    args_matched += 1
                elif argument["name"] == "Name" and argument["value"] == "VBOX__":
                    args_matched += 1

            # Finally, if everything went well, I consider the signature as matched.
            if args_matched == 2:
                return True
