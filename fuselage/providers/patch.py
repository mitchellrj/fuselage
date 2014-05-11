# Copyright 2011-2014 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from fuselage import error, resources, provider
from fuselage.changes import EnsureFile


class Patch(provider.Provider):

    """ Provides file creation using templates or static files. """

    policies = (resources.patch.PatchApplyPolicy,)

    def check_path(self, ctx, directory, simulate):
        if os.path.isdir(directory):
            return
        frags = directory.split("/")
        path = "/"
        for i in frags:
            path = os.path.join(path, i)
            if not os.path.exists(path):  # FIXME
                if not simulate:
                    raise error.PathComponentMissing(path)
            elif not os.path.isdir(path):
                raise error.PathComponentNotDirectory(path)

    def get_patch(self, context):
        patch = context.get_file(self.resource.patch)
        data = patch.read()
        # FIXME: Would be good to validate the patch here a bit
        return data, "secret" in patch.labels

    def apply_patch(self, context):
        patch, sensitive = self.get_patch(context)

        cmd = 'patch -t --dry-run -N --silent -r - -o - %s -' % self.resource.source
        returncode, stdout, stderr = context.transport.execute(
            cmd, stdin=patch)

        if returncode != 0:
            self.logger.error("Patch does not apply cleanly")
            self.logger.error(
                "Patch file used was %s" % self.resource.patch)
            self.logger.error(
                "File to patch was %s" % self.resource.source)

            self.logger.error("")
            self.logger.error("Reported error was:")
            map(self.logger.error, stderr.split("\n"))

            raise error.CommandError("Unable to apply patch")

        return stdout, sensitive

    def apply(self, context):
        name = self.resource.name

        self.check_path(context, os.path.dirname(name), context.simulate)

        contents, sensitive = self.apply_patch(context)

        fc = EnsureFile(name, contents, self.resource.owner,
                        self.resource.group, self.resource.mode, sensitive)
        context.change(fc)

        return fc.changed
