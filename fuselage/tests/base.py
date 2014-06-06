# Copyright 2014 Isotoma Limited
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

import inspect
import os
import unittest
import logging
import mock
import fakechroot

from fuselage import bundle, runner, error, platform
from .recorder import Player, Recorder


logger = logging.getLogger()


class TestCaseWithBundle(unittest.TestCase):

    def setUp(self):
        self.bundle = bundle.ResourceBundle()


class TestCaseWithRunner(TestCaseWithBundle):

    location = os.path.join(os.path.dirname(__file__), "..", "..")

    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)

        self.logger = logging.getLogger(__name__)

        path = inspect.getfile(self.__class__).rsplit(".", 1)[0] + ".json"
        id = self.id()

        if os.environ.get("FUSELAGE_RECORD", None):
            self.chroot = fakechroot.FakeChroot.create_in_tempdir(self.location)
            self.chroot.build()
            self.cassette = Recorder(path, id)
            logger.debug("Created fakechroot @ %s" % self.chroot.chroot_path)
        else:
            self.chroot = mock.Mock()
            self.cassette = Player(path, id)

        self.patches = []

        def patch(name, fn):
            self.cassette.register(name, fn)

            p = mock.patch("fuselage.platform.%s" % name, spec=True)
            self.patches.append(p)
            patch = p.start()
            patch.side_effect = getattr(self.cassette, name)
            return p

        for meth in ("isfile", "islink", "lexists", "get", "put", "makedirs", "unlink", "exists", "isdir", "readlink", "stat", "lstat", "getgrall", "getgrnam", "getgrgid", "getpwall", "getpwnam", "getpwuid", "getspall", "getspnam"):
            patch(meth, getattr(self.chroot, meth))

        orig_check_call = platform.check_call

        def check_call(command, *args, **kwargs):
            env = kwargs.pop('env', {})
            env.update(self.chroot.get_env())
            kwargs['env'] = env

            gid = kwargs.pop('gid', None)
            group = kwargs.pop('group', None)
            if group:
                gid = self.chroot.getgrnam(group).gr_gid
            if gid:
                env['FAKEROOTGID'] = env['FAKEROOTEGID'] = str(gid)
                env['FAKEROOTSGID'] = env['FAKEROOTFGID'] = str(gid)

            uid = kwargs.pop('uid', None)
            user = kwargs.pop('user', None)
            if user:
                uid = self.chroot.getpwnam(user).pw_uid
            if uid:
                env['FAKEROOTUID'] = env['FAKEROOTEUID'] = str(uid)
                env['FAKEROOTSUID'] = env['FAKEROOTFUID'] = str(uid)

            cwd = kwargs.get('cwd', None)
            kwargs['cwd'] = os.path.join(self.chroot.chroot_path, cwd.lstrip("/")) if cwd else self.chroot.chroot_path

            paths = [self.chroot.overlay_dir]
            if "PATH" in env:
                paths.extend(os.path.join(env["FAKECHROOT_BASE"], p.lstrip("/")) for p in env["PATH"].split(":"))
                for p in paths:
                    path = os.path.join(p, command[0])
                    if os.path.exists(path):
                        command[0] = path
                        break

            return orig_check_call(command, *args, **kwargs)

        patch("check_call", check_call)

        logger.debug("Patched platform layer with fakechroot monkeypatches")

        self.bundle = bundle.ResourceBundle()

    def tearDown(self):
        [p.stop() for p in self.patches]
        logger.debug("Monkey patches reverted")

        if self.chroot:
            self.chroot.destroy()
            logger.debug("Fakechroot destroyed")

        self.cassette.save()

    def failUnlessExists(self, path):
        if not platform.exists(path):
            self.fail("Path '%s' does not exist" % path)

    def failIfExists(self, path):
        if platform.exists(path):
            self.fail("Path '%s' exists" % path)

    def apply(self, simulate=False):
        r = runner.Runner(self.bundle, simulate=simulate)
        return r.run()

    def check_apply(self):
        logger.debug("Simulating bundle apply")
        self.apply(simulate=True)

        logger.debug("Applying bundle")
        try:
            self.apply(simulate=False)
        except error.NothingChanged:
            self.fail("Their were no pending changes after simulate")

        logger.debug("Applying bundle again to check for idempotency")
        try:
            self.apply(simulate=False)
        except error.NothingChanged:
            return
        else:
            self.fail("After 2nd apply() their were still pending changes")
