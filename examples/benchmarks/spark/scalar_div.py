import salmon.lang as sal
from salmon.comp import dagonly
from salmon.utils import *
from salmon.codegen import CodeGenConfig, spark


def scalar_div():

    @dagonly
    def protocol():

        colsInA = [
            defCol('a', 'INTEGER', [1]),
            defCol('b', 'INTEGER', [1]),
            defCol('c', 'INTEGER', [1]),
            defCol('d', 'INTEGER', [1])
        ]

        in1 = sal.create("in1", colsInA, set([1]))
        div1 = sal.divide(in1, 'div1', 'a', [5])

        return set([in1])

    dag = protocol()
    config = CodeGenConfig('scalar_div_spark')
    cg = spark.SparkCodeGen(config, dag)
    cg.generate('scalar_div_spark', '/tmp')

if __name__ == "__main__":

    scalar_div()

