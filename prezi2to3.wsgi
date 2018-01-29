import os
# Change working directory so relative paths (and template lookup) work again
os.chdir(os.path.dirname(__file__))

import bottle
from twoToThreeUpgraderService import Service
# ... build or import your bottle application here ...
# Do NOT use bottle.run() with mod_wsgi
s = Service()
application = s.get_bottle_app()
