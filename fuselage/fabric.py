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

from __future__ import absolute_import
import six

from fabric import tasks
from fabric.operations import put, sudo

from fuselage import bundle, builder


class DeploymentTask(tasks.WrappedCallableTask):

    def run(self, *args, **kwargs):
        bun = bundle.ResourceBundle()
        iterator = self.wrapped(*args, **kwargs)
        while True:
            try:
                bun.add(iterator.next())
            except StopIteration:
                break
            except Exception as e:
                # Throw the exception inside the wrapped function for easier debugging
                iterator.throw(e)

        buffer = six.BytesIO()
        buffer.name = self.name

        bu = builder.Builder.write_to(buffer)
        bu.embed_fuselage_runtime()
        bu.embed_resource_bundle(bun)
        bu.close()

        put(buffer, '~/payload.pex', mode=0755)
        sudo('~/payload.pex')

    def __call__(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)


def blueprint(*args, **kwargs):
    """
    Decorator declaring the wrapped function to be a resource generator that should be deployed.

    May be invoked as a simple, argument-less decorator (i.e. ``@blueprint``) or
    with arguments customizing its behavior (e.g. ``@blueprint(alias='myalias')``).
    """
    invoked = bool(not args or kwargs)
    if not invoked:
        func, args = args[0], ()

    task_class = kwargs.pop("task_class", DeploymentTask)

    def wrapper(func):
        return task_class(func, *args, **kwargs)

    return wrapper if invoked else wrapper(func)
