import salmon.lang as sal
from salmon.comp import dagonly
from salmon.utils import *
from salmon.codegen import CodeGenConfig, spark


def col_mult():

    @dagonly
    def protocol():

        colsInA = [
            defCol('a', 'INTEGER', [1]),
            defCol('b', 'INTEGER', [1]),
            defCol('c', 'INTEGER', [1]),
            defCol('d', 'INTEGER', [1])
        ]

        in1 = sal.create("in1", colsInA, set([1]))
        mult1 = sal.multiply(in1, 'mult1', 'a', ['a', 'b'])

        return set([in1])

    dag = protocol()
    config = CodeGenConfig('col_mult_spark')
    cg = spark.SparkCodeGen(config, dag)
    cg.generate('col_mult_spark', '/tmp')

if __name__ == "__main__":

    col_mult()

