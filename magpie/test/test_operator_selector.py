from magpie.base import EpsilonGreedy

def test_quality_assignment():
    selector = EpsilonGreedy(['op1', 'op2'], 0.1)

    # Variant 1
    op = 'op1'
    instruction_count1 = 100 # Our fitness
    selector.update_quality(op, -instruction_count1)
    assert selector._average_qualities[op] == -instruction_count1

    # Variant 2
    op = 'op1'
    instruction_count2 = 200 # Our fitness
    selector.update_quality(op, -instruction_count2)
    assert selector._average_qualities[op] == - (instruction_count1 + instruction_count2) / 2

    assert selector._action_count['op2'] == 0, "Op2 should not have been updated"