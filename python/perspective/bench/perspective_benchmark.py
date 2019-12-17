################################################################################
#
# Copyright (c) 2019, the Perspective Authors.
#
# This file is part of the Perspective library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#

import os
import sys
from functools import partial
from bench import Benchmark, Suite, Runner
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..'))
from perspective import Table  # noqa: E402

SUPERSTORE_ARROW = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..",
    "examples",
    "simple",
    "superstore.arrow")


def make_meta(group, name):
    return {
        "group": group,
        "name": name,
        "version": "master"
    }


class PerspectiveBenchmark(Suite):

    AGG_OPTIONS = [
        [{"column": "Sales", "op": "sum"}],
        [{"column": "State", "op": "dominant"}],
        [{"column": "Order Date", "op": "dominant"}]
    ]
    COLUMN_PIVOT_OPTIONS = [[], ["Sub-Category"], ["Category", "Sub-Category"]]
    ROW_PIVOT_OPTIONS = [[], ["State"], ["State", "City"]]

    VERSION = "master"

    def __init__(self):
        """Create a benchmark suite for `perspective-python`."""
        with open(SUPERSTORE_ARROW, "rb") as arrow:
            tbl = Table(arrow.read())
            self._view = tbl.view()
            self.dict = self._view.to_dict()
            self.records = self._view.to_records()
            self.numpy = self._view.to_numpy()
            self.csv = self._view.to_csv()
            self.arrow = self._view.to_arrow()
            self._table = tbl

    def register_benchmarks(self):
        """Register all the benchmark methods - each method creates a number of
        lambdas, and then calls `setattr` on the Suite itself so that the
        `Runner` can find the tests at runtime."""
        self.benchmark_table()
        self.benchmark_view_zero()
        self.benchmark_view_one()
        self.benchmark_view_two()
        self.benchmark_view_two_column_only()
        self.benchmark_to_format()

    def benchmark_table(self):
        """Benchmark table creation from different formats."""
        for name in ("dict", "records", "numpy"):
            data = getattr(self, name)
            test_meta = make_meta("table", name)
            func = Benchmark(lambda: Table(data), meta=test_meta)
            setattr(self, "table_{0}".format(name), func)

    def benchmark_view_zero(self):
        """Benchmark view creation with zero pivots."""
        func = Benchmark(self._table.view, meta=make_meta("view", "zero"))
        setattr(self, "view_zero", func)

    def benchmark_view_one(self):
        """Benchmark view creation with different pivots."""
        for pivot in PerspectiveBenchmark.ROW_PIVOT_OPTIONS:
            if len(pivot) == 0:
                continue
            test_meta = make_meta("view", "one_{0}_pivot".format(len(pivot)))
            view_constructor = partial(self._table.view, row_pivots=pivot)
            func = Benchmark(view_constructor, meta=test_meta)
            setattr(self, "view_{0}".format(test_meta["name"]), func)

    def benchmark_view_two(self):
        """Benchmark view creation with row and column pivots."""
        for i in range(len(PerspectiveBenchmark.ROW_PIVOT_OPTIONS)):
            RP = PerspectiveBenchmark.ROW_PIVOT_OPTIONS[i]
            CP = PerspectiveBenchmark.COLUMN_PIVOT_OPTIONS[i]
            if len(RP) == 0 and len(CP) == 0:
                continue
            test_meta = make_meta("view", "two_{0}x{1}_pivot".format(len(RP), len(CP)))
            view_constructor = partial(
                self._table.view, row_pivots=RP, column_pivots=CP)
            func = Benchmark(view_constructor, meta=test_meta)
            setattr(self, "view_{0}".format(test_meta["name"]), func)

    def benchmark_view_two_column_only(self):
        """Benchmark column-only view creation."""
        for pivot in PerspectiveBenchmark.COLUMN_PIVOT_OPTIONS:
            test_meta = make_meta(
                "view", "two_column_only_{0}_pivot".format(len(pivot)))
            view_constructor = partial(self._table.view, column_pivots=pivot)
            func = Benchmark(view_constructor, meta=test_meta)
            setattr(self, "view_{0}".format(test_meta["name"]), func)

    def benchmark_to_format(self):
        """Benchmark each `to_format` method."""
        for name in ("numpy", "dict", "records", "df"):
            test_meta = make_meta("to_format", name)
            func = Benchmark(
                getattr(self._view, "to_{0}".format(name)), meta=test_meta)
            setattr(self, "to_format_{0}".format(name), func)


if __name__ == "__main__":
    # Initialize a suite and runner, then call `.run()`
    suite = PerspectiveBenchmark()
    runner = Runner(suite)
    runner.run()
