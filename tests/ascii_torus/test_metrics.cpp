#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>
#include <vector>
#include "mcik/experiments/ascii_torus/metrics.hpp"

TEST_CASE("ASCII quality estimator is deterministic on fixed buffer") {
  const int w = 8, h = 4;
  std::vector<char> buf(w * h, ' ');
  for (int x = 0; x < w; ++x) buf[(h / 2) * w + x] = '#';
  double q1 = torus_metrics::estimate_ascii_quality(buf, w, h);
  double q2 = torus_metrics::estimate_ascii_quality(buf, w, h);
  REQUIRE(q1 == Approx(q2));
}
