# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from typing import Iterator

import alchy
import sqlalchemy as sqa

from cgstats.db import api, models

LOG = logging.getLogger(__name__)


class StatsAPI(alchy.Manager):

    Project = models.Project
    Sample = models.Sample
    Unaligned = models.Unaligned
    Supportparams = models.Supportparams
    Datasource = models.Datasource
    Demux = models.Demux
    Flowcell = models.Flowcell

    def __init__(self, config: dict):
        alchy_config = dict(SQLALCHEMY_DATABASE_URI=config['cgstats']['database'])
        super(StatsAPI, self).__init__(config=alchy_config, Model=models.Model)
        self.root_dir = Path(config['cgstats']['root'])

    def flowcell(self, flowcell_name: str) -> dict:
        """Fetch information about a flowcell."""
        record = self.Flowcell.query.filter_by(flowcellname=flowcell_name).first()
        data = {
            'name': record.flowcellname,
            'sequencer': record.demux[0].datasource.machine,
            'sequencer_type': record.hiseqtype,
            'date': record.time,
            'samples': []
        }
        for sample_obj in self.flowcell_samples(record):
            raw_samplename = sample_obj.name.split('_', 1)[0]
            curated_samplename = raw_samplename.rstrip('AB')
            sample_data = { 
                'name': curated_samplename,
                'reads': 0,
                'fastqs': [],
            }
            for flowcell_obj in self.sample_reads(sample_obj):
                if flowcell_obj.type == 'hiseqga' and flowcell_obj.q30 >= 80:
                    sample_data['reads'] += flowcell_obj.reads
                elif flowcell_obj.type == 'hiseqx' and flowcell_obj.q30 >= 75:
                    sample_data['reads'] += flowcell_obj.reads
                else:
                    LOG.warning(f"q30 too low for {curated_samplename} on {flowcell_obj.name}:"
                                f"{flowcell_obj.q30} < {80 if flowcell_obj.type == 'hiseqga' else 75}%")
                    continue
                for fastq_path in self.fastqs(flowcell_obj, sample_obj):
                    sample_data['fastqs'].append(str(fastq_path))

        return data

    def flowcell_samples(self, flowcell_obj: models.Flowcell) -> Iterator[models.Sample]:
        """Fetch all the samples from a flowcell."""
        return (
            self.Sample.query
            .join(models.Sample.unaligned, models.Unaligned.demuxes)
            .filter(models.Demux.flowcell == flowcell_obj)
        )

    def sample_flowcells(self, sample_obj: models.Sample) -> Iterator[models.Flowcell]:
        """Fetch all flowcells for a sample."""
        return (
            self.Flowcell.query
            .join(models.Flowcell.demux, models.Demux.unaligned)
            .filter(models.Unaligned.sample == sample_obj)
        )

    def sample_reads(self, sample_obj: models.Sample) -> Iterator:
        """Calculate reads for a sample."""
        query = (
            self.session.query(
                models.Flowcell.flowcellname.label('name'),
                models.Flowcell.hiseqtype.label('type'),
                sqa.func.sum(models.Unaligned.readcounts).label('reads'),
                sqa.func.min(models.Unaligned.q30).label('q30'),
            )
            .join(
                models.Flowcell.demuxes,
                models.Demux.unaligned
            )
            .filter(models.Unaligned.sample == sample_obj)
            .group_by(models.Flowcell.flowcellname)
        )
        return query

    def sample(self, sample_name: str) -> models.Sample:
        """Fetch a sample for the database by name."""
        return api.get_sample(sample_name).first()

    def fastqs(self, flowcell_obj: models.Flowcell, sample_obj: models.Sample) -> Iterator[Path]:
        """Fetch FASTQ files for a sample."""
        base_pattern = "*{}/Unaligned*/Project_*/Sample_{}/*.fastq.gz"
        alt_pattern = "*{}/Unaligned*/Project_*/Sample_{}_*/*.fastq.gz"
        for fastq_pattern in (base_pattern, alt_pattern):
            pattern = fastq_pattern.format(flowcell_obj.flowcellname, sample_obj.samplename)
            files = self.root_dir.glob(pattern)
            yield from files
