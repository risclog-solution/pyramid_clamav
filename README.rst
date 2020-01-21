pyramid_clamav
==============

Pyramid tween which checks file uploads for viruses using clamav.

You need to have a running clamav installation on your system to which
the tween can connect via a unix socket. You can set the socket path in
your config (pyramid_clamav.socket), but the defaults should work on most
systems.

If you want to deactivate scanning (i.e. for testing or your local development
environment), you can set pyramid_clamav.debug to a value. Then flash- and 
logmessages are generated if there was a file upload *and* clamav is not 
properly configured.

If a virus was found, the file is removed from the request. The field which
was used to upload the file should handle it like no file was uploaded.

A flashmessage is presented to the user stating that a file contained a virus
and it has been removed.

It should also work for multiple files.


This project was conceived by Daniel Havlik (dh@gocept.com).
