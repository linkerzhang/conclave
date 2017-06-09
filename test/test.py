import salmon.lang as sal 
from salmon.comp import mpc, scotch

def testAgg():
    @scotch
    @mpc
    def protocol():

        # define inputs
        colsIn1 = [
            ("INTEGER", set([1])),
            ("INTEGER", set([1]))
        ]
        in1 = sal.create("in1", colsIn1, set([1]))
        colsIn2 = [
            ("INTEGER", set([2])), 
            ("INTEGER", set([2]))
        ]
        in2 = sal.create("in2", colsIn2, set([2]))
        
        # combine parties' inputs into one relation
        rel = sal.concat([in1, in2], "rel")

        # specify the workflow
        projA = sal.project(rel, "projA", ["rel_0", "rel_1"])
        projB = sal.project(projA, "projB", ["projA_0", "projA_1"])
        agg = sal.aggregate(projB, "agg", "projB_0", "projB_1", "+")

        opened = sal.collect(agg, "opened", 1)

        # return root nodes
        return set([in1, in2])

    expected = """CREATE RELATION in1 {1} WITH COLUMNS (INTEGER, INTEGER)
CREATE RELATION in2 {2} WITH COLUMNS (INTEGER, INTEGER)
PROJECT [in1_0, in1_1] FROM (in1 {1}) AS projA_0 {1}
PROJECT [in2_0, in2_1] FROM (in2 {2}) AS projA_1 {2}
PROJECT [projA_0_0, projA_0_1] FROM (projA_0 {1}) AS projB_0 {1}
AGG [projB_0_1, +] FROM (projB_0 {1}) GROUP BY [projB_0_0] AS agg_0 {1}
PROJECT [projA_1_0, projA_1_1] FROM (projA_1 {2}) AS projB_1 {2}
AGG [projB_1_1, +] FROM (projB_1 {2}) GROUP BY [projB_1_0] AS agg_1 {2}
CONCATMPC [agg_0 {1}, agg_1 {2}] AS rel {1, 2}
AGGMPC [rel_1, +] FROM (rel {1, 2}) GROUP BY [rel_0] AS agg_obl {1}
STORE RELATION agg_obl {1} INTO {1} AS opened
"""
    actual = protocol()
    assert expected == actual

def testAggProj():

    @scotch
    @mpc
    def protocol():

        # define inputs
        colsIn1 = [
            ("INTEGER", set([1])),
            ("INTEGER", set([1]))
        ]
        in1 = sal.create("in1", colsIn1, set([1]))
        colsIn2 = [
            ("INTEGER", set([2])), 
            ("INTEGER", set([2]))
        ]
        in2 = sal.create("in2", colsIn2, set([2]))
        
        # combine parties' inputs into one relation
        rel = sal.concat([in1, in2], "rel")

        # specify the workflow
        projA = sal.project(rel, "projA", ["rel_0", "rel_1"])
        projB = sal.project(projA, "projB", ["projA_0", "projA_1"])
        agg = sal.aggregate(projB, "agg", "projB_0", "projB_1", "+")
        projC = sal.project(agg, "projC", ["agg_0", "agg_1"])

        opened = sal.collect(projC, "opened", 1)

        # return root nodes
        return set([in1, in2])

    expected = """CREATE RELATION in1 {1} WITH COLUMNS (INTEGER, INTEGER)
CREATE RELATION in2 {2} WITH COLUMNS (INTEGER, INTEGER)
PROJECT [in1_0, in1_1] FROM (in1 {1}) AS projA_0 {1}
PROJECT [in2_0, in2_1] FROM (in2 {2}) AS projA_1 {2}
PROJECT [projA_0_0, projA_0_1] FROM (projA_0 {1}) AS projB_0 {1}
AGG [projB_0_1, +] FROM (projB_0 {1}) GROUP BY [projB_0_0] AS agg_0 {1}
PROJECT [projA_1_0, projA_1_1] FROM (projA_1 {2}) AS projB_1 {2}
AGG [projB_1_1, +] FROM (projB_1 {2}) GROUP BY [projB_1_0] AS agg_1 {2}
CONCATMPC [agg_0 {1}, agg_1 {2}] AS rel {1, 2}
AGGMPC [rel_1, +] FROM (rel {1, 2}) GROUP BY [rel_0] AS agg_obl {1}
PROJECT [agg_obl_0, agg_obl_1] FROM (agg_obl {1}) AS projC {1}
STORE RELATION projC {1} INTO {1} AS opened
"""
    actual = protocol()
    assert expected == actual

def testConcat():

    @scotch
    @mpc
    def protocol():

        # define inputs
        colsIn1 = [
            ("INTEGER", set([1])), 
            ("INTEGER", set([1]))
        ]
        in1 = sal.create("in1", colsIn1, set([1]))
        colsIn2 = [
            ("INTEGER", set([2])), 
            ("INTEGER", set([2]))
        ]
        in2 = sal.create("in2", colsIn2, set([2]))
        colsIn3 = [
            ("INTEGER", set([3])), 
            ("INTEGER", set([3]))
        ]
        in3 = sal.create("in3", colsIn3, set([3]))

        # combine parties' inputs into one relation
        rel = sal.concat([in1, in2, in3], "rel")

        opened = sal.collect(rel, "opened", 1)

        # return root nodes
        return set([in1, in2, in3])

    expected = """CREATE RELATION in1 {1} WITH COLUMNS (INTEGER, INTEGER)
CREATE RELATION in2 {1} WITH COLUMNS (INTEGER, INTEGER)
CREATE RELATION in3 {1} WITH COLUMNS (INTEGER, INTEGER)
CONCAT [in1 {1}, in2 {1}, in3 {1}] AS rel {1}
STORE RELATION rel {1} INTO {1} AS opened
"""
    actual = protocol()
    assert expected == actual

def testInternalAgg():

    @scotch
    @mpc
    def protocol():
        # define inputs
        colsInA = [
            ("INTEGER", set([1])), 
            ("INTEGER", set([1]))
        ]
        inA = sal.create("inA", colsInA, set([1]))
        colsInB = [
            ("INTEGER", set([2])), 
            ("INTEGER", set([2]))
        ]
        inB = sal.create("inB", colsInB, set([2]))

        # specify the workflow
        projA = sal.project(inA, "projA", ["inA_0", "inA_1"])
        projB = sal.project(inB, "projB", ["inB_0", "inB_1"])
        joined = sal.join(projA, projB, "joined", "projA_0", "projB_0")
        agg = sal.aggregate(joined, "agg", "joined_0", "joined_1", "+")
        proj = sal.project(agg, "proj", ["agg_0", "agg_1"])

        opened = sal.collect(proj, "opened", 1)

        return set([inA, inB])

    expected = """CREATE RELATION inA {1} WITH COLUMNS (INTEGER, INTEGER)
CREATE RELATION inB {2} WITH COLUMNS (INTEGER, INTEGER)
PROJECT [inA_0, inA_1] FROM (inA {1}) AS projA {1}
PROJECT [inB_0, inB_1] FROM (inB {2}) AS projB {2}
(projA {1}) JOINMPC (projB {2}) ON projA_0 AND projB_0 AS joined {1, 2}
AGGMPC [joined_1, +] FROM (joined {1, 2}) GROUP BY [joined_0] AS agg {1}
PROJECT [agg_0, agg_1] FROM (agg {1}) AS proj {1}
STORE RELATION proj {1} INTO {1} AS opened
"""
    actual = protocol()
    assert expected == actual

def testJoin():

    @scotch
    @mpc
    def protocol():
        # define inputs
        colsInA = [
            ("INTEGER", set([1])), 
            ("INTEGER", set([1]))
        ]
        inA = sal.create("inA", colsInA, set([1]))

        colsInB = [
            ("INTEGER", set([2])),
            ("INTEGER", set([2]))
        ]
        inB = sal.create("inB", colsInB, set([2]))

        # specify the workflow
        aggA = sal.aggregate(inA, "aggA", "inA_0", "inA_1", "+")
        projA = sal.project(aggA, "projA", ["aggA_0", "aggA_1"])
        
        aggB = sal.aggregate(inB, "aggB", "inB_0", "inB_1", "+")
        projB = sal.project(aggB, "projB", ["aggB_0", "aggB_1"])
        
        joined = sal.join(projA, projB, "joined", "projA_0", "projB_0")

        proj = sal.project(joined, "proj", ["joined_0", "joined_1"])
        agg = sal.aggregate(
            proj, "agg", "proj_0", "proj_1", "+")

        opened = sal.collect(agg, "opened", 1)

        # create dag
        return set([inA, inB])

    expected = """CREATE RELATION inA {1} WITH COLUMNS (INTEGER, INTEGER)
AGG [inA_1, +] FROM (inA {1}) GROUP BY [inA_0] AS aggA {1}
CREATE RELATION inB {2} WITH COLUMNS (INTEGER, INTEGER)
AGG [inB_1, +] FROM (inB {2}) GROUP BY [inB_0] AS aggB {2}
PROJECT [aggA_0, aggA_1] FROM (aggA {1}) AS projA {1}
PROJECT [aggB_0, aggB_1] FROM (aggB {2}) AS projB {2}
(projA {1}) JOINMPC (projB {2}) ON projA_0 AND projB_0 AS joined {1, 2}
PROJECTMPC [joined_0, joined_1] FROM (joined {1, 2}) AS proj {1, 2}
AGGMPC [proj_1, +] FROM (proj {1, 2}) GROUP BY [proj_0] AS agg {1}
STORE RELATION agg {1} INTO {1} AS opened
"""
    actual = protocol()
    assert expected == actual

def testJoinConcat():

    @scotch
    @mpc
    def protocol():
        # define inputs
        colsInA = [
            ("INTEGER", set([2])), 
            ("INTEGER", set([2]))
        ]
        inA = sal.create("inA", colsInA, set([2]))

        colsInB = [
            ("INTEGER", set([3])),
            ("INTEGER", set([3]))
        ]
        inB = sal.create("inB", colsInB, set([3]))

        colsInC = [
            ("INTEGER", set([1])),
            ("INTEGER", set([1])),
            ("INTEGER", set([1]))
        ]
        inC = sal.create("inC", colsInC, set([1]))

        # specify the workflow
        aggA = sal.aggregate(inA, "aggA", "inA_0", "inA_1", "+")
        projA = sal.project(aggA, "projA", ["aggA_0", "aggA_1"])
        
        aggB = sal.aggregate(inB, "aggB", "inB_0", "inB_1", "+")
        projB = sal.project(aggB, "projB", ["aggB_0", "aggB_1"])
        
        joined = sal.join(projA, projB, "joined", "projA_0", "projB_0")
        comb = sal.concat([inC, joined], "comb")
        opened = sal.collect(comb, "opened", 1)

        # create dag
        return set([inA, inB, inC])

    expected = """CREATE RELATION inA {2} WITH COLUMNS (INTEGER, INTEGER)
AGG [inA_1, +] FROM (inA {2}) GROUP BY [inA_0] AS aggA {2}
CREATE RELATION inB {3} WITH COLUMNS (INTEGER, INTEGER)
AGG [inB_1, +] FROM (inB {3}) GROUP BY [inB_0] AS aggB {3}
CREATE RELATION inC {1} WITH COLUMNS (INTEGER, INTEGER, INTEGER)
PROJECT [aggA_0, aggA_1] FROM (aggA {2}) AS projA {2}
PROJECT [aggB_0, aggB_1] FROM (aggB {3}) AS projB {3}
(projA {2}) JOINMPC (projB {3}) ON projA_0 AND projB_0 AS joined {1}
CONCAT [inC {1}, joined {1}] AS comb {1}
STORE RELATION comb {1} INTO {1} AS opened
"""
    actual = protocol()
    assert expected == actual, actual

def testJoinConcat2():

    @scotch
    @mpc
    def protocol():
        # define inputs
        colsInA = [
            ("INTEGER", set([2])), 
            ("INTEGER", set([2]))
        ]
        inA = sal.create("inA", colsInA, set([2]))

        colsInB = [
            ("INTEGER", set([3])),
            ("INTEGER", set([3]))
        ]
        inB = sal.create("inB", colsInB, set([3]))

        colsInC = [
            ("INTEGER", set([1])),
            ("INTEGER", set([1])),
            ("INTEGER", set([1]))
        ]
        inC = sal.create("inC", colsInC, set([1]))

        # specify the workflow
        aggA = sal.aggregate(inA, "aggA", "inA_0", "inA_1", "+")
        projA = sal.project(aggA, "projA", ["aggA_0", "aggA_1"])
        
        aggB = sal.aggregate(inB, "aggB", "inB_0", "inB_1", "+")
        projB = sal.project(aggB, "projB", ["aggB_0", "aggB_1"])
        
        joined = sal.join(projA, projB, "joined", "projA_0", "projB_0")
        comb = sal.concat([inC, joined], "comb")
        agg = sal.aggregate(comb, "agg", "comb_1", "comb_2", "+")
        opened = sal.collect(agg, "opened", 1)

        # create dag
        return set([inA, inB, inC])

    expected = """CREATE RELATION inA {2} WITH COLUMNS (INTEGER, INTEGER)
AGG [inA_1, +] FROM (inA {2}) GROUP BY [inA_0] AS aggA {2}
CREATE RELATION inB {3} WITH COLUMNS (INTEGER, INTEGER)
AGG [inB_1, +] FROM (inB {3}) GROUP BY [inB_0] AS aggB {3}
CREATE RELATION inC {1} WITH COLUMNS (INTEGER, INTEGER, INTEGER)
PROJECT [aggA_0, aggA_1] FROM (aggA {2}) AS projA {2}
PROJECT [aggB_0, aggB_1] FROM (aggB {3}) AS projB {3}
(projA {2}) JOINMPC (projB {3}) ON projA_0 AND projB_0 AS joined {2, 3}
CONCATMPC [inC {1}, joined {2, 3}] AS comb {1, 2, 3}
AGGMPC [comb_2, +] FROM (comb {1, 2, 3}) GROUP BY [comb_1] AS agg {1}
STORE RELATION agg {1} INTO {1} AS opened
"""
    actual = protocol()
    assert expected == actual, actual

def testMultAgg():

    @scotch
    @mpc
    def protocol():

        # define inputs
        colsIn1 = [
            ("INTEGER", set([1])), 
            ("INTEGER", set([1]))
        ]
        in1 = sal.create("in1", colsIn1, set([1]))
        colsIn2 = [
            ("INTEGER", set([2])), 
            ("INTEGER", set([2]))
        ]
        in2 = sal.create("in2", colsIn2, set([2]))
        
        # combine parties' inputs into one relation
        rel = sal.concat([in1, in2], "rel")

        # specify the workflow
        projA = sal.project(rel, "projA", ["rel_0", "rel_1"])
        aggA = sal.aggregate(projA, "aggA", "projA_0", "projA_1", "+")
        
        projB = sal.project(rel, "projB", ["rel_0", "rel_1"])
        aggB = sal.aggregate(projB, "aggB", "projB_0", "projB_1", "+")

        openedA = sal.collect(aggA, "openedA", 1)
        openedB = sal.collect(aggB, "openedB", 1)

        # return root nodes
        return set([in1, in2])

    expected = """CREATE RELATION in1 {1} WITH COLUMNS (INTEGER, INTEGER)
CREATE RELATION in2 {2} WITH COLUMNS (INTEGER, INTEGER)
PROJECT [in1_0, in1_1] FROM (in1 {1}) AS projA_0 {1}
AGG [projA_0_1, +] FROM (projA_0 {1}) GROUP BY [projA_0_0] AS aggA_0 {1}
PROJECT [in2_0, in2_1] FROM (in2 {2}) AS projA_1 {2}
AGG [projA_1_1, +] FROM (projA_1 {2}) GROUP BY [projA_1_0] AS aggA_1 {2}
PROJECT [in1_0, in1_1] FROM (in1 {1}) AS projB_0 {1}
AGG [projB_0_1, +] FROM (projB_0 {1}) GROUP BY [projB_0_0] AS aggB_0 {1}
PROJECT [in2_0, in2_1] FROM (in2 {2}) AS projB_1 {2}
AGG [projB_1_1, +] FROM (projB_1 {2}) GROUP BY [projB_1_0] AS aggB_1 {2}
CONCATMPC [aggA_0 {1}, aggA_1 {2}] AS rel {1, 2}
AGGMPC [rel_1, +] FROM (rel {1, 2}) GROUP BY [rel_0] AS aggA_obl {1}
STORE RELATION aggA_obl {1} INTO {1} AS openedA
CONCATMPC [aggB_0 {1}, aggB_1 {2}] AS rel_1 {1, 2}
AGGMPC [rel_1_1, +] FROM (rel_1 {1, 2}) GROUP BY [rel_1_0] AS aggB_obl {1}
STORE RELATION aggB_obl {1} INTO {1} AS openedB
"""
    actual = protocol()
    assert expected == actual, actual

def testMultiple():

    @scotch
    @mpc
    def protocol():

        # define inputs
        colsIn1 = [
            ("INTEGER", set([1])), 
            ("INTEGER", set([1]))
        ]
        in1 = sal.create("in1", colsIn1, set([1]))
        colsIn2 = [
            ("INTEGER", set([2])), 
            ("INTEGER", set([2]))
        ]
        in2 = sal.create("in2", colsIn2, set([2]))
        
        # combine parties' inputs into one relation
        rel = sal.concat([in1, in2], "rel")

        # specify the workflow
        projA = sal.project(rel, "projA", ["rel_0", "rel_1"])
        projB = sal.project(rel, "projB", ["rel_0", "rel_1"])

        opened = sal.collect(projA, "opened", 1)
        opened = sal.collect(projB, "opened", 1)

        # return root nodes
        return set([in1, in2])

    expected = """CREATE RELATION in1 {1} WITH COLUMNS (INTEGER, INTEGER)
CREATE RELATION in2 {2} WITH COLUMNS (INTEGER, INTEGER)
PROJECT [in1_0, in1_1] FROM (in1 {1}) AS projA_0 {1}
PROJECT [in2_0, in2_1] FROM (in2 {2}) AS projA_1 {1}
PROJECT [in1_0, in1_1] FROM (in1 {1}) AS projB_0 {1}
PROJECT [in2_0, in2_1] FROM (in2 {2}) AS projB_1 {1}
CONCAT [projA_0 {1}, projA_1 {1}] AS rel {1}
STORE RELATION rel {1} INTO {1} AS opened
CONCAT [projB_0 {1}, projB_1 {1}] AS rel_1 {1}
STORE RELATION rel_1 {1} INTO {1} AS opened
"""
    actual = protocol()
    assert expected == actual, actual

def testSingle():

    @scotch
    @mpc
    def protocol():

        # define inputs
        colsIn1 = [
            ("INTEGER", set([1])), 
            ("INTEGER", set([1]))
        ]
        in1 = sal.create("in1", colsIn1, set([1]))
        colsIn2 = [
            ("INTEGER", set([2])), 
            ("INTEGER", set([2]))
        ]
        in2 = sal.create("in2", colsIn2, set([2]))
        colsIn3 = [
            ("INTEGER", set([3])), 
            ("INTEGER", set([3]))
        ]
        in3 = sal.create("in3", colsIn3, set([3]))

        # combine parties' inputs into one relation
        rel = sal.concat([in1, in2, in3], "rel")

        # specify the workflow
        projA = sal.project(rel, "projA", ["rel_0", "rel_1"])
        projB = sal.project(projA, "projB", ["projA_0", "projA_1"])

        opened = sal.collect(projB, "opened", 1)

        # return root nodes
        return set([in1, in2, in3])

    expected = """CREATE RELATION in1 {1} WITH COLUMNS (INTEGER, INTEGER)
CREATE RELATION in2 {2} WITH COLUMNS (INTEGER, INTEGER)
CREATE RELATION in3 {3} WITH COLUMNS (INTEGER, INTEGER)
PROJECT [in1_0, in1_1] FROM (in1 {1}) AS projA_0 {1}
PROJECT [in2_0, in2_1] FROM (in2 {2}) AS projA_1 {2}
PROJECT [in3_0, in3_1] FROM (in3 {3}) AS projA_2 {3}
PROJECT [projA_0_0, projA_0_1] FROM (projA_0 {1}) AS projB_0 {1}
PROJECT [projA_1_0, projA_1_1] FROM (projA_1 {2}) AS projB_1 {1}
PROJECT [projA_2_0, projA_2_1] FROM (projA_2 {3}) AS projB_2 {1}
CONCAT [projB_0 {1}, projB_1 {1}, projB_2 {1}] AS rel {1}
STORE RELATION rel {1} INTO {1} AS opened
"""
    actual = protocol()
    assert expected == actual, actual

if __name__ == "__main__":

    testAgg()
    testAggProj()
    testConcat()
    testInternalAgg()
    testJoin()
    testJoinConcat()
    testJoinConcat2()
    testMultAgg()
    testMultiple()
    testSingle()
