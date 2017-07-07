# -*- coding: utf-8 -*-
from cg.apps.lims import ClinicalLims
from cg.store import Store
from .schema import ExternalProject, FastqProject, RerunProject, ScoutProject


class OrdersAPI(object):

    projects = {
        'external': ExternalProject,
        'fastq': FastqProject,
        'rerun': RerunProject,
        'scout': ScoutProject,
    }

    def __init__(self, lims: ClinicalLims, status: Store):
        self.lims = lims
        self.status = status

    def accept(self, project_type: str, data: dict) -> dict:
        """Accept a new project."""
        errors = self.validate(project_type, data)
        if errors:
            return errors
        lims_data = self.to_lims(data)
        lims_project = self.lims.add_project(lims_data)
        lims_samples = self.lims.get_samples(projectlimsid=lims_project.id)
        lims_map = {lims_sample.name: lims_sample.id for lims_sample in lims_samples}
        status_data = self.to_status(data, lims_map)
        new_families = self.status.add_order(status_data)
        self.status.add_commit(new_families)
        return {
            'lims_project': lims_project,
            'families': new_families,
        }

    @classmethod
    def validate(cls, project_type: str, data: dict):
        """Validate input against a particular schema."""
        errors = cls.projects[project_type].validate(data)
        return errors

    @staticmethod
    def to_lims(data: dict) -> dict:
        """Convert order input to lims interface input."""
        lims_data = {
            'name': data['name'],
            'samples': [],
        }
        for family in data['families']:
            for sample in family['samples']:
                lims_data['samples'].append({
                    'name': sample['name'],
                    'container': sample['container'],
                    'container_name': sample['container_name'],
                    'udfs': {
                        'priority': family['priority'],
                        'application_tag': sample['application_tag'],
                        'require_qcok': family['require_qcok'],
                        'well_position': sample['well_position'],
                        'quantity': sample['quantity'],
                        'source': sample['source'],
                        'customer': data['customer'],
                    }
                })
        return lims_data

    @staticmethod
    def to_status(data: dict, lims_map: dict) -> dict:
        """Convert order input to status interface input."""
        status_data = {
            'customer': data['customer'],
            'families': [{
                'name': family['name'],
                'priority': family['priority'],
                'panels': family['panels'],
                'samples': [{
                    'lims_id': lims_map[sample['name']],
                    'name': sample['name'],
                    'sex': sample['sex'],
                    'status': sample['status'],
                    'mother': sample.get('mother'),
                    'father': sample.get('father'),
                } for sample in family['samples']]
            } for family in data['families']]
        }
        return status_data