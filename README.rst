LinkPreview: A middleware for EFB
=================================

Notice
------

**Middleware ID**: ``catbaron.link_preview``

**LinkPreview** is a middleware for EFB to generqate link preview.

You need to use **MessageBlocker** on top of
`EFB <https://ehforwarderbot.readthedocs.io>`__. Please check the
document and install EFB first.

Dependense
----------

-  Python >=3.6
-  EFB >=2.0.0b15

Install
-------

-  Install

   ::

       git clone https://github.com/catbaron0/efb-link_preview-middleware
       cd efb-link_preview-middleware
       sudo python setup.py install

-  Register to EFB Following `this
   document <https://ehforwarderbot.readthedocs.io/en/latest/getting-started.html>`__
   to edit the config file. The config file by default is
   ``~/.ehforwarderbot/profiles/default``. It should look like:

::

    master_channel: foo.demo_master
    slave_channels:
    - foo.demo_slave
    - bar.dummy
    middlewares:
    - foo.other_middlewares
    - catbaron.link_preview

You only need to add the last line to your config file.

-  Restart EFB.
