# -*- coding: utf-8 -*-
import datetime as dt
from pathlib import Path

import pytest

from cg.store import Store


@pytest.yield_fixture(scope='function')
def store() -> Store:
    _store = Store(uri='sqlite://')
    _store.create_all()
    yield _store
    _store.drop_all()

@pytest.yield_fixture(scope='function')
def base_store(store):
    """Setup and example store."""
    customers = [store.add_customer('cust000', 'Production', scout=False),
                 store.add_customer('cust001', 'Customer', scout=False),
                 store.add_customer('cust002', 'Karolinska', scout=True),
                 store.add_customer('cust003', 'CMMS', scout=True)]
    store.add_commit(customers)
    applications = [store.add_application('WGXCUSC000', 'wgs', 'External WGS', sequencing_depth=0, is_external=True),
                    store.add_application('EXXCUSR000', 'wes', 'External WES', sequencing_depth=0, is_external=True),
                    store.add_application('WGSPCFC060', 'wgs', 'WGS, double', sequencing_depth=30,
                                          accredited=True),
                    store.add_application('RMLS05R150', 'rml', 'Ready-made', sequencing_depth=0),
                    store.add_application('WGTPCFC030', 'wgs', 'WGS trio', accredited=True,
                                          sequencing_depth=30, target_reads=300000000)]
    store.add_commit(applications)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    versions = [store.add_version(application, 1, valid_from=dt.datetime.now(), prices=prices)
                for application in applications]
    store.add_commit(versions)

    yield store


@pytest.yield_fixture(scope='function')
def disk_store(cli_runner, invoke_cli) -> Store:
    database = './test_db.sqlite3'
    database_path = Path(database)
    database_uri = f"sqlite:///{database}"
    with cli_runner.isolated_filesystem():
        assert database_path.exists() is False

        # WHEN calling "init"
        result = invoke_cli(['--database', database_uri, 'init'])

        # THEN it should setup the database with some tables
        assert result.exit_code == 0
        assert database_path.exists()
        assert len(Store(database_uri).engine.table_names()) > 0

        yield Store(database_uri)
