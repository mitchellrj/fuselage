.. _resources:

=========
Resources
=========

This section describes the core resources you can use to describe your server configuration.

File
====

A provider for this resource will create or amend an existing file to the
provided specification.

For example, the following will create the /etc/hosts file based on a static
local file::

    File(
        name="/etc/hosts",
        owner="root",
        group="root"
        mode=0o644,
        source="my_hosts_file",
    )

The available parameters are:

``name``
    The full path to the file this resource represents.
``owner``
    A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module.
``group``
    A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module.
``mode``
    A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work.
``source``
    An optional file that is rendered into ``name`` on the target. Fuselage
    searches the searchpath to find it.
``contents``
    The arguments passed to the renderer.


Directory
---------

A directory on disk. Directories have limited metadata, so this resource is
quite limited.

For example::

    extend resources:
      - Directory:
          name: /var/local/data
          owner: root
          group: root
          mode: 0755

The available parameters are:

``name``
    The full path to the directory on disk
``owner``
    The unix username who should own this directory, by default this is 'root'
``group``
    The unix group who should own this directory, by default this is 'root'
``mode``
    The octal mode that represents this directory's permissions, by default
    this is '755'.
``parents``
    Create parent directories as needed, using the same ownership and
    permissions, this is False by default.


Link
----

A resource representing a symbolic link. The link will be from `name` to `to`.
If you specify owner, group and/or mode then these settings will be applied to
the link itself, not to the object linked to.

For example::

    extend resources:
      - Link:
          name: /etc/init.d/exampled
          to: /usr/local/example/sbin/exampled
          owner: root
          group: root

The available parameters are:

``name``
    The name of the file this resource represents.
``owner``
    A unix username or UID who will own created objects. An owner that
    begins with a digit will be interpreted as a UID, otherwise it will be
    looked up using the python 'pwd' module.
``group``
    A unix group or GID who will own created objects. A group that begins
    with a digit will be interpreted as a GID, otherwise it will be looked up
    using the python 'grp' module.
``to``
    The pathname to which to link the symlink. Dangling symlinks ARE
    considered errors in Fuselage.


Execute
-------

Execute a command. This command *is* executed in a shell subprocess.

For example::

    extend resources:
      - Execute:
          name: core_packages_apt_key
          command: apt-key adv --keyserver keyserver.ubuntu.com --recv-keys {{source.key}}

A much more complex example. This shows executing a command if a checkout
synchronises::

    extend resources:
      for bi in flavour.base_images:
        - Execute:
            name: base-image-{{bi}}
            policy:
              execute:
                  when: sync
                  on: /var/local/checkouts/ci
            command: ./vmbuilder-{{bi}}
            cwd: /var/local/checkouts/ci
            user: root

The available parameters are:

``name``
    The name of this resource. This should be unique and descriptive, and
    is used so that resources can reference each other.
``command``
    If you wish to run a single command, then this is the command.
``commands``
    If you wish to run multiple commands, provide a list
``cwd``
    The current working directory in which to execute the command.
``environment``
    The environment to provide to the command, for example::

        extend resources:
          - Execute:
              name: example
              command: echo $FOO
              environment:
                  FOO: bar

``returncode``
    The expected return code from the command, defaulting to 0. If the
    command does not return this return code then the resource is considered
    to be in error.
``user``
    The user to execute the command as.
``group``
    The group to execute the command as.
``umask``
    The umask to use when executing this command
``unless``
    A command to run to determine is this execute should be actioned
``creates``
    The full path to a file that execution of this command creates. This
    is used like a "touch test" in a Makefile. If this file exists then the
    execute command will NOT be executed.
``touch``
    The full path to a file that fuselage will touch once this command has
    completed successfully. This is used like a "touch test" in a Makefile. If
    this file exists then the execute command will NOT be executed.


Checkout
--------

This represents a "working copy" from a Source Code Management system.
This could be provided by, for example, Subversion or Git remote
repositories.

Note that this is '*a* checkout', not 'to checkout'. This represents the
resource itself on disk. If you change the details of the working copy
(for example changing the branch) the provider will execute appropriate
commands (such as ``svn switch``) to take the resource to the desired state.

For example::

    extend resources:
      - Checkout:
          name: /usr/src/myapp
          repository: https://github.com/myusername/myapp
          scm: git

The available parameters are:

``name``
    The full path to the working copy on disk.
``repository``
    The identifier for the repository - this could be an http url for
    subversion or a git url for git, for example.
``branch``
    The name of a branch to check out, if required.
``tag``
    The name of a tag to check out, if required.
``revision``
    The revision to check out or move to.
``scm``
    The source control management system to use, e.g. subversion, git.
``scm_username``
    The username for the remote repository
``scm_password``
    The password for the remote repository.
``user``
    The user to perform actions as, and who will own the resulting files.
    The default is root.
``group``
    The group to perform actions as. The default is to use the primary group of
    ``user``.
``mode``
    A mode representation as an octal. This can begin with leading zeros if
    you like, but this is not required. DO NOT use yaml Octal representation
    (0o666), this will NOT work.


Package
-------

Represents an operating system package, installed and managed via the
OS package management system. For example, to ensure these three packages
are installed::

    extend resources:
      - Package:
          name: apache2

The available parameters are:

``name``
    The name of the package. This can be a single package or a list can be
    supplied.
``version``
    The version of the package, if only a single package is specified and
    the appropriate provider supports it (the Apt provider does not support
    it).
``purge``
    When removing a package, whether to purge it or not.

When installing a package ``apt-get`` may give a ``404`` error if your local
apt cache is stale. If Fuselage thinks this might be the cause it will ``apt-get
update`` and retry before giving up.


User
----

A resource representing a UNIX user in the password database. The underlying
implementation currently uses the "useradd" and "usermod" commands to implement
this resource.

This resource can be used to create, change or delete UNIX users.

For example::

    extend resources:
      - User:
          name: django
          fullname: Django Software Owner
          home: /var/local/django
          system: true
          disabled-password: true

The available parameters are:

``name``
    The username this resource represents.
``password``
    The encrypted password, as returned by crypt(3). You should make sure
    this password respects the system's password policy.
``fullname``
    The comment field for the password file - generally used for the user's
    full name.
``home``
    The full path to the user's home directory.
``uid``
    The user identifier for the user. This must be a non-negative integer.
``gid``
    The group identifier for the user. This must be a non-negative integer.
``group``
    The primary group for the user, if you wish to specify it by name.
``groups``
    A list of supplementary groups that the user should be a member of.
``append``
    A boolean that sets how to apply the groups a user is in. If true then
    fuselage will add the user to groups as needed but will not remove a user from
    a group. If false then fuselage will replace all groups the user is a member
    of. Thus if a process outside of fuselage adds you to a group, the next
    deployment would remove you again.
``system``
    A boolean representing whether this user is a system user or not. This only
    takes effect on creation - a user cannot be changed into a system user once
    created without deleting and recreating the user.
``shell``
    The full path to the shell to use.
``disabled_password``
    A boolean for whether the password is locked for this account.
``disabled_login``
    A boolean for whether this entire account is locked or not.


Group
-----

A resource representing a unix group stored in the /etc/group file.
``groupadd`` and ``groupmod`` are used to actually make modifications.

For example::

    extend resources:
      - Group:
          name: zope
          system: true

The available parameters are:

``name``
    The name of the unix group.
``gid``
    The group ID associated with the group. If this is not specified one will
    be chosen.
``system``
    Whether or not this is a system group - i.e. the new group id will be
    taken from the system group id list.
``password``
    The password for the group, if required


Service
-------

This represents service startup and shutdown via an init daemon.

The available parameters are:

``name``
    A unique name representing an initd service. This would normally match the
    name as it appears in /etc/init.d.
``priority``
    Priority of the service within the boot order. This attribute will have no
    effect when using a dependency or event based init.d subsystem like upstart
    or systemd.
``start``
    A command that when executed will start the service. If not provided, the
    provider will use the default service start invocation for the init.d
    system in use.
``stop``
    A command that when executed will start the service. If not provided, the
    provider will use the default service stop invocation for the init.d system
    in use.
``restart``
    A command that when executed will restart the service. If not provided, the
    provider will use the default service restart invocation for the init.d
    system in use. If it is not possible to automatically determine if the restart
    script is avilable the service will be stopped and started instead.
``reconfig``
    A command that when executed will make the service reload its
    configuration file.
``running``
    A comamnd to execute to determine if a service is running. Should have an
    exit code of 0 for success.
``pidfile``
    Where the service creates its pid file. This can be provided instead of
    ``running``  as an alternative way of checking if a service is running or not.


Dependencies between resources
==============================

Resources are always applied in the order they are listed in the resources property. You can rely on this to build repeatble and reliable processes. However this might not be enough. There are a couple of other ways to express relationships between resources.

One example is when you want to run a script only if you have deployed a new version of your code::

    resources:
      - Checkout:
          name: /usr/local/src/mycheckout
          repository: git://github.com/example/example_project

      - Execute:
          name: install-requirements
          command: /var/sites/myapp/bin/pip install -r /usr/local/src/mycheckout/requirements.txt
          policy:
              execute:
                  when: sync
                  on: Checkout[/usr/local/src/mycheckout]

When the ``Checkout`` step pulls in a change from a repository, the ``Execute`` resource will apply its ``execute`` policy.

You can do the same for monitoring file changes too::

    resources:
      - File:
          name: /etc/apache2/security.conf
          static: apache2/security.conf

      - Execute:
          name: restart-apache
          commands:
            - apache2ctl configtest
            - apache2ctl graceful
          policy:
              execute:
                  when: apply
                  on: File[/etc/apache2/security.conf]

Sometimes you can't use ``File`` (perhaps ``buildout`` or ``maven`` or similar generates a config file for you), but you still want to trigger a command when a file changes during deployment::

    resources:
      - Execute:
          name: buildout
          command: buildout -c production.cfg
          watches:
            - /var/sites/mybuildout/parts/apache.cfg

      - Execute:
          name: restart-apache
          commands:
            - apache2ctl configtest
            - apache2ctl graceful
          policy:
              execute:
                  when: watched
                  on: File[/var/sites/mybuildout/parts/apache.cfg]

This declares that the ``buildout`` step might change a ``File`` (the ``apache.cfg``). Subsequent step can then subscribe to ``File[/var/sites/mybuildout/parts/apache.cfg]`` as though it was an ordinary file.

All of these examples use a trigger system. When a trigger has been set fuselage will remember it between invocations. Consider the following example::

    resources:
      - File:
          name: /etc/apache2/sites-enabled/mydemosite

      - Directory:
          name: /var/local/tmp/this/paths/parent/dont/exist

      - Execute:
          name: restart-apache2
          command: /etc/init.d/apache2 restart
          policy:
              execute:
                  when: apply
                  on: File[/etc/apache2/sites-enabled/mydemosite]

When it is run it will create a file in the ``/etc/apache2/sites-enabled`` folder. Fuselage knows that the ``Execute[restart-apache2]`` step must be run later. It will record a trigger for the ``Execute`` statement in ``/var/run/yaybu/``. If the ``Directory[]`` step fails and fuselage terminates then the next time fuselage is execute it will instruct you to use the ``--resume`` or ``--no-resume`` command line option. If you ``--resume`` it will remember that it needs to restart apache2. If you choose ``--no-resume`` it will not remember, and apache will not be restarted.
