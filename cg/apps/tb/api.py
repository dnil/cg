# -*- coding: utf-8 -*-
import datetime as dt
import logging
import shutil
from pathlib import Path
from typing import List

import click
import ruamel.yaml
from trailblazer.mip.start import MipCli
from trailblazer.store import Store, models
from trailblazer.cli.utils import environ_email
from trailblazer.mip import files, fastq, trending

from .add import AddHandler

log = logging.getLogger(__name__)


class TrailblazerAPI(Store, AddHandler, fastq.FastqHandler):
    """Interface to Trailblazer for `cg`."""

    parse_sampleinfo = staticmethod(files.parse_sampleinfo)

    def __init__(self, config: dict):
        super(TrailblazerAPI, self).__init__(
            config['trailblazer']['database'],
            families_dir=config['trailblazer']['root'],
        )
        self.mip_cli = MipCli(config['trailblazer']['script'])
        self.mip_config = config['trailblazer']['mip_config']

    def start(self, family_id: str, priority: str = 'normal', email: str = None,
              skip_evaluation: bool = False, start_with = None):
        """Start MIP."""
        email = email or environ_email()
        kwargs = dict(config=self.mip_config, family=family_id, priority=priority, email=email, start_with=start_with)
        if skip_evaluation:
            kwargs['skip_evaluation'] = True
        self.mip_cli(**kwargs)
        for old_analysis in self.analyses(family=family_id):
            old_analysis.is_deleted = True
        self.commit()
        self.add_pending(family_id, email=email)

    def get_sampleinfo(self, analysis: models.Analysis) -> str:
        """Get the sample info path for an analysis."""
        raw_data = ruamel.yaml.safe_load(Path(analysis.config_path).open())
        data = files.parse_config(raw_data)
        return data['sampleinfo_path']

    @staticmethod
    def parse_qcmetrics(data: dict) -> dict:
        """Call internal Trailblazer MIP API."""
        return files.parse_qcmetrics(data)

    def write_panel(self, family_id: str, content: List[str]):
        """Write the gene panel to the defined location."""
        out_dir = Path(self.families_dir) / family_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / 'aggregated_master.bed'
        with out_path.open('w') as out_handle:
            for line in content:
                click.echo(line, file=out_handle)

    def delete_analysis(self, family: str, date: dt.datetime, yes: bool = False):
        """Delete the analysis output."""
        if self.analyses(family=family, temp=True).count() > 0:
            raise ValueError("analysis for family already running")
        analysis_obj = self.find_analysis(family, date, 'completed')
        assert analysis_obj.is_deleted is False
        analysis_path = Path(analysis_obj.out_dir).parent

        if yes or click.confirm(f"Do you want to remove {analysis_path}?"):
            shutil.rmtree(analysis_path, ignore_errors=True)

            analysis_obj.is_deleted = True
            self.commit()

    def get_trending(self, mip_config_raw: str, qcmetrics_raw: str, sampleinfo_raw: dict) -> dict:
        return trending.parse_mip_analysis(mip_config_raw= mip_config_raw,
                                           qcmetrics_raw=qcmetrics_raw,
                                           sampleinfo_raw=sampleinfo_raw)

    def get_family_root_dir(self, family_id: str):
        return Path(self.families_dir) / family_id
