from twisted.application.service import ServiceMaker

import diamondash

DEFAULT_STRPORT = 'tcp:8000'

serviceMaker = ServiceMaker('diamondash', 'diamondash.server', 'diamondash', 'diamondash')
