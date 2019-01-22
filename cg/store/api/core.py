# -*- coding: utf-8 -*-
import logging

import alchy

from cg.store import models
from cg.store.api.find2 import FindHandler2

from .add import AddHandler
from .find import FindHandler
from .status import StatusHandler
from .trends import TrendsHandler

LOG = logging.getLogger(__name__)


class CoreHandler(AddHandler, FindHandler, FindHandler2, StatusHandler, TrendsHandler):
    """Aggregating class for the store api handlers"""
    pass


class Store(alchy.Manager, CoreHandler):

    def __init__(self, uri):
        self.uri = uri
        super(Store, self).__init__(config=dict(SQLALCHEMY_DATABASE_URI=uri), Model=models.Model)
