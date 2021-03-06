# -*- coding: utf-8 -*-
"""Test get MIP files"""

from pathlib import Path

from cg.apps.tb.add import AddHandler


def test_get_files(files_data) -> dict:
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN config data of a "sharp" run (not dry run)
    mip_config = files_data['config']

    # GIVEN sampleinfo input from a finished analysis
    sampleinfo = files_data['sampleinfo']

    mip_file_data = AddHandler._get_files(mip_config, sampleinfo)

    # Define test data
    mip_file_test_data = {
        'mip-config': {
            'path': mip_config['config_path'],
        },
        'sampleinfo': {
            'path': mip_config['sampleinfo_path'],
        },
        'pedigree': {
            'path': sampleinfo['pedigree_path'],
        },
        'mip-log': {
            'path': mip_config['log_path'],
        },
        'qcmetrics': {
            'path': sampleinfo['qcmetrics_path'],
        },
        'snv-gbcf': {
            'path': sampleinfo['snv']['gbcf'],
        },
        'snv-gbcf-index': {
            'path': f"{sampleinfo['snv']['gbcf']}.csi",
        },
        'snv-bcf': {
            'path': sampleinfo['snv']['bcf'],
        },
        'snv-bcf-index': {
            'path': f"{sampleinfo['snv']['bcf']}.csi",
        },
        'sv-bcf': {
            'path': sampleinfo['sv']['bcf'],
        },
        'sv-bcf-index': {
            'path': f"{sampleinfo['sv']['bcf']}.csi",
        },
        'ped-check': {
            'path': sampleinfo['peddy']['ped_check'],
        },
        'ped': {
            'path': sampleinfo['peddy']['ped'],
        },
        'sex-check': {
            'path': sampleinfo['peddy']['sex_check'],
        },
        'vcf-snv-clinical': {
            'path': sampleinfo['snv']['clinical_vcf'],
        },
        'vcf-snv-clinical-index': {
            'path': f"{sampleinfo['snv']['clinical_vcf']}.tbi",
        },
        'vcf-sv-clinical': {
            'path': sampleinfo['sv']['clinical_vcf'],
        },
        'vcf-sv-clinical-index': {
            'path': f"{sampleinfo['sv']['clinical_vcf']}.tbi",
        },
        'vcf-snv-research': {
            'path': sampleinfo['snv']['research_vcf'],
        },
        'vcf-snv-research-index': {
            'path': f"{sampleinfo['snv']['research_vcf']}.tbi",
        },
        'vcf-sv-research': {
            'path': sampleinfo['sv']['research_vcf'],
        },
        'vcf-sv-research-index': {
            'path': f"{sampleinfo['sv']['research_vcf']}.tbi",
        },
    }

    ## Check returns from def
    ## Family data
    for tag_id in mip_file_test_data:
        # For every file tag
        for key, value in mip_file_test_data[tag_id].items():
            # For each element
            for element_data in mip_file_data:
                # If file tag exists in the return data tags
                if tag_id in element_data['tags']:
                    assert value in element_data[key]


    mip_file_test_sample_data = {}

    ## Define sample test data
    for sample_data in sampleinfo['samples']:

        ## Bam preprocessing
        bam_path = sample_data['bam']
        bai_path = f"{bam_path}.bai"
        if not Path(bai_path).exists():
            bai_path = bam_path.replace('.bam', '.bai')
        mip_file_test_sample_data[sample_data['id']] = {
            'bam': bam_path,
            'bam-index': bai_path,
            'coverage': sample_data['sambamba'],
            'vcf2cytosure': sample_data['vcf2cytosure'],
        }

        ## Only wgs data
        ## Downsamples MT bam
        if sample_data['subsample_mt']:
            mt_bam_path = sample_data['subsample_mt']
            mt_bai_path = f"{mt_bam_path}.bai"
            if not Path(mt_bai_path).exists():
                mt_bai_path = mt_bam_path.replace('.bam', '.bai')
            mip_file_test_sample_data[sample_data['id']]['bam-mt'] = mt_bam_path
            mip_file_test_sample_data[sample_data['id']]['bam-mt-index'] = mt_bai_path 

    ## Check returns from def
    ## Sample data
    for sample_id in mip_file_test_sample_data:
        for key, value in mip_file_test_sample_data[sample_id].items():
            for element_data in mip_file_data:
                # If file tag exists in the return data tags
                if sample_id and key in element_data['tags']:
                    assert value in element_data['path']
