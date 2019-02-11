"""This file tests the samples_to_sequence part of the status api"""

from cg.store import Store


def test_samples_to_sequence(sample_store: Store):
    """Test that we get which samples are in queue to be sequenced"""

    # GIVEN a store with sample in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.sequenced_at]) >= 1

    # WHEN finding which samples are in queue to be sequenced
    sequence_samples = sample_store.samples_to_sequence()

    # THEN it should list the received and partly sequenced samples
    assert sequence_samples.count() == 2
    assert {sample.name for sample in sequence_samples} == set(['sequenced-partly', 'received-prepared'])
    for sample in sequence_samples:
        assert sample.sequenced_at is None
        if sample.name == 'sequenced-partly':
            assert sample.reads > 0
