"""
Unit tests for rangeproofs.

TODO: Add tests for failure conditions of PowerTwoRangeStmt

"""
import pytest

from petlib.bn import Bn
from petlib.ec import EcGroup

from zksk import Secret
from zksk.pairings import BilinearGroupPair
from zksk.primitives.rangeproof import PowerTwoRangeStmt, RangeStmt, RangeOnlyStmt
from zksk.primitives.rangeproof import decompose_into_n_bits
from zksk.utils import make_generators
from zksk.utils.debug import SigmaProtocol


def test_decompose_n_bits():
    n4 = Bn(4)
    assert decompose_into_n_bits(n4, 4) == [0, 0, 1, 0]

    n3 = Bn(3)
    assert decompose_into_n_bits(n3, 6) == [1, 1, 0, 0, 0, 0]

    n5 = Bn(5)
    assert decompose_into_n_bits(n5, 4) == [1, 0, 1, 0]


def test_decompose_n_bits_too_big():
    n4 = Bn(9)
    with pytest.raises(Exception):
        decompose_into_n_bits(n4, 3)


def test_decompose_n_bits_negative():
    n4 = Bn(-2)
    with pytest.raises(Exception):
        decompose_into_n_bits(n4, 3)


def test_power_two_range_stmt_non_interactive():
    group_pair = BilinearGroupPair()
    group = group_pair.G1

    value = Secret(value=Bn(10))
    randomizer = Secret(value=group.order().random())

    g, h = make_generators(2, group)
    limit = 20

    com = value * g + randomizer * h

    p1 = PowerTwoRangeStmt(com.eval(), g, h, limit, value, randomizer)
    p2 = PowerTwoRangeStmt(com.eval(), g, h, limit, Secret(), Secret())

    tr = p1.prove()
    assert p2.verify(tr)


def test_power_two_range_stmt_interactive():
    group_pair = BilinearGroupPair()
    group = group_pair.G1

    value = Secret(value=Bn(10))
    randomizer = Secret(value=group.order().random())

    g, h = make_generators(2, group)
    limit = 20

    com = value * g + randomizer * h

    p1 = PowerTwoRangeStmt(com.eval(), g, h, limit, value, randomizer)
    p2 = PowerTwoRangeStmt(com.eval(), g, h, limit, Secret(), Secret())

    (p1 & p2).get_prover()

    prover = p1.get_prover()
    verifier = p2.get_verifier()
    protocol = SigmaProtocol(verifier, prover)
    assert protocol.verify()
    verifier.stmt.full_validate()


def test_range_stmt_non_interactive_start_at_zero(group):
    x = Secret(value=3)
    randomizer = Secret(value=group.order().random())

    g, h = make_generators(2, group)
    lo = 0
    hi = 5

    com = x * g + randomizer * h
    stmt = RangeStmt(com.eval(), g, h, lo, hi, x, randomizer)

    tr = stmt.prove()
    assert stmt.verify(tr)


def test_range_stmt_non_interactive_start_at_nonzero(group):
    x = Secret(value=14)
    randomizer = Secret(value=group.order().random())

    g, h = make_generators(2, group)
    lo = 6
    hi = 16

    com = x * g + randomizer * h

    stmt1 = RangeStmt(com.eval(), g, h, lo, hi, x, randomizer)
    tr = stmt1.prove()

    stmt2 = RangeStmt(com.eval(), g, h, lo, hi, Secret(), Secret())
    assert stmt2.verify(tr)


def test_range_stmt_non_interactive_outside_range(group):
    x = Secret(value=15)
    randomizer = Secret(value=group.order().random())

    g, h = make_generators(2, group)
    lo = 7
    hi = 15

    com = x * g + randomizer * h

    with pytest.warns(UserWarning):
        stmt = RangeStmt(com.eval(), g, h, lo, hi, x, randomizer)


def test_range_stmt_non_interactive_wrong_commit(group):
    x = Secret(value=14)
    randomizer = Secret(value=group.order().random())

    g, h = make_generators(2, group)
    lo = 7
    hi = 15

    com = x * g + randomizer * h
    comval = com.eval() + g
    stmt = RangeStmt(comval, g, h, lo, hi, x, randomizer)

    tr = stmt.prove()

    with pytest.raises(Exception):
        assert not stmt.verify(tr)


def test_range_proof_outside():
    group = EcGroup()
    x = Secret(value=15)
    randomizer = Secret(value=group.order().random())

    g, h = make_generators(2, group)
    lo = 0
    hi = 14

    com = x * g + randomizer * h
    with pytest.raises(Exception):
        stmt = RangeStmt(com.eval(), g, h, lo, hi, x, randomizer)
        nizk = stmt.prove()
        stmt.verify(nizk)


def test_range_proof_outside_range_above():
    x = Secret(value=7)
    lo = 0
    hi = 6
    with pytest.raises(Exception):
        stmt = RangeOnlyStmt(lo, hi, x)
        nizk = stmt.prove()
        assert stmt.verify(nizk) == False


def test_range_proof_outside_range_below():
    x = Secret(value=1)
    lo = 2
    hi = 7

    with pytest.raises(Exception):
        stmt = RangeOnlyStmt(lo, hi, x)
        nizk = stmt.prove()
        stmt.verify(nizk)
