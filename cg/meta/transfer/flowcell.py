# -*- coding: utf-8 -*-
import logging
from typing import List

from cg.store import models, Store
from cg.apps.stats import StatsAPI, models as stats_models
from cg.apps.hk import HousekeeperAPI

log = logging.getLogger(__name__)


class TransferFlowcell():

    def __init__(self, db: Store, stats_api: StatsAPI, hk_api: HousekeeperAPI):
        self.db = db
        self.stats = stats_api
        self.hk = hk_api

    def transfer(self, flowcell_name: str) -> models.Flowcell:
        """Populate the database with the information."""
        stats_data = self.stats.flowcell(flowcell_name)
        record = self.db.flowcell(flowcell_name)
        if record is None:
            record = self.db.add_flowcell(
                name=flowcell_name,
                sequencer=stats_data['sequencer'],
                sequenced=stats_data['date'],
            )
        for sample_data in stats_data['samples']:
            log.debug(f"adding reads to sample: {sample_data['name']}")
            sample_obj = self.db.sample(sample_data['name'])
            if sample_obj is None:
                log.warning(f"unable to find sample: {sample_data['name']}")
                continue

            # store FASTQ files
            fastq_files = self.stats.fastqs(sample_obj)
            self.store_fastqs(sample_obj.internal_id, fastq_files)

            sample_obj.reads = sample_data['reads']
            enough_reads = (sample_obj.reads >
                            sample_obj.application_version.application.expected_reads)
            newest_date = ((sample_obj.sequenced_at is None) or
                           (record.sequenced_at > sample_obj.sequenced_at))
            if enough_reads and newest_date:
                sample_obj.sequenced_at = record.sequenced_at
            record.samples.append(sample_obj)
            log.info(f"added reads to sample: {sample_data['name']} - {sample_data['reads']} "
                     f"[{'DONE' if enough_reads else 'NOT DONE'}]")

        return record

    def store_fastqs(self, sample_id: str, fastq_files: List[str]):
        """Store FASTQ files for a sample in housekeeper."""
        hk_bundle = self.hk.bundle(sample_id)
        if hk_bundle is None:
            new_bundle = self.hk.new_bundle(sample_id)
            self.hk.add_commit(new_bundle)
            new_version = self.hk.new_version(created_at=new_bundle.created_at)
            new_version.bundle = new_bundle
            self.hk.add_commit(new_version)

        for fastq_file in fastq_files:
            if self.hk.files(path=fastq_file).first() is None:
                log.info(f"found FASTQ file: {fastq_file}")
                new_file = self.hk.new_file(path=fastq_file, tags=[self.hk.tag('fastq')])
                new_file.version = hk_bundle.versions[0]
                self.hk.add(new_file)
        self.hk.commit()
