# Copyright (C) 2015 Optiv, Inc. (brad.spengler@optiv.com)
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

from lib.cuckoo.common.abstracts import Signature

class DeadLink(Signature):
    name = "dead_link"
    description = "Attempts to execute a binary from a dead or sinkholed URL"
    severity = 3
    weight = 2
    categories = ["generic"]
    authors = ["Optiv"]
    minimum = "1.2"
    evented = True

    def __init__(self, *args, **kwargs):
        Signature.__init__(self, *args, **kwargs)
        self.appnames = []

    filter_apinames = set(["CreateProcessInternalW"])

    def on_call(self, call, process):
        appname = self.get_argument(call, "ApplicationName").lower()
        if appname not in self.appnames:
            self.appnames.append(appname)

    def on_complete(self):
        if "dropped" in self.results:
            deadnames = []
            for dropped in self.results["dropped"]:
                if "HTML document" not in dropped["type"]:
                    continue
                lowerpaths = map(str.lower, dropped["guest_paths"])
                for appname in self.appnames:
                    if appname in lowerpaths:
                        deadnames.append(appname)
                        break
            if deadnames:
                for deadname in deadnames:
                    self.data.append({"dead_binary" : deadname})
                return True

        return False