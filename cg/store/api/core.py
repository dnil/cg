# -*- coding: utf-8 -*-
import logging

import alchy

from cg.store import models
from cg.store.api.reset import ResetHandler

from .add import AddHandler
from .find import FindHandler
from .status import StatusHandler
from .trends import TrendsHandler

LOG = logging.getLogger(__name__)


class BaseHandler:

    User = models.User
    Customer = models.Customer
    CustomerGroup = models.CustomerGroup
    Sample = models.Sample
    Family = models.Family
    FamilySample = models.FamilySample
    Flowcell = models.Flowcell
    Analysis = models.Analysis
    Application = models.Application
    ApplicationVersion = models.ApplicationVersion
    Panel = models.Panel
    Pool = models.Pool
    Delivery = models.Delivery
    Invoice = models.Invoice
    MicrobialSample = models.MicrobialSample
    MicrobialOrder = models.MicrobialOrder
    Organism = models.Organism


class CoreHandler(BaseHandler, AddHandler, FindHandler, StatusHandler, TrendsHandler, ResetHandler):
    pass


class Store(alchy.Manager, CoreHandler):

    def __init__(self, uri):
        self.uri = uri
        super(Store, self).__init__(config=dict(SQLALCHEMY_DATABASE_URI=uri), Model=models.Model)
