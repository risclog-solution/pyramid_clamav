pyramid_clamav
==============

Pyramid tween which checks file uploads for viruses using clamav.
Inspired by Julien Danjou (http://julien.danjou.info/blog/2013/extending-swift-with-a-middleware-clamav).

If a virus was found, 403 Forbidden is raised.
