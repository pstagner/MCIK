#pragma once
#include <algorithm>
#include <cmath>
#include <vector>

namespace torus_metrics {

inline double char_density(char c) {
  // Rough luminance ranking: space (dark) to '@' (bright)
  static const char* ramp = " .:-=+*#%@";
  const int n = 10;
  for (int i = 0; i < n; ++i) if (ramp[i] == c) return (double)i / (double)(n - 1);
  // fallback: normalized ASCII code (coarse)
  unsigned uc = static_cast<unsigned>(static_cast<unsigned char>(c));
  return std::clamp((uc - 32.0) / (126.0 - 32.0), 0.0, 1.0);
}

inline double estimate_ascii_quality(const std::vector<char>& buf, int w, int h) {
  if (w < 3 || h < 3) return 0.0;
  double acc = 0.0;
  int cnt = 0;
  for (int y = 1; y < h - 1; ++y) {
    for (int x = 1; x < w - 1; ++x) {
      int off = y * w + x;
      double cx1 = char_density(buf[off - 1]);
      double cx2 = char_density(buf[off + 1]);
      double cy1 = char_density(buf[off - w]);
      double cy2 = char_density(buf[off + w]);
      double gx = 0.5 * (cx2 - cx1);
      double gy = 0.5 * (cy2 - cy1);
      double g = std::sqrt(gx * gx + gy * gy);
      acc += g;
      cnt++;
    }
  }
  if (cnt == 0) return 0.0;
  // Higher average gradient suggests clearer edges; clamp to [0,1]
  double avg = acc / (double)cnt;           // typical range ~[0,1]
  double q = std::clamp(avg, 0.0, 1.0);
  return q;
}

inline double estimate_ascii_similarity(const std::vector<char>& buf,
                                        const std::vector<char>& ref,
                                        int w, int h) {
  // Inverted MSE in density space: 1 - mean((d - d_ref)^2)
  if (buf.size() != ref.size() || (int)buf.size() != w * h) return 0.0;
  double acc = 0.0;
  int cnt = w * h;
  for (int i = 0; i < cnt; ++i) {
    double d = char_density(buf[i]);
    double r = char_density(ref[i]);
    double e = d - r;
    acc += e * e;
  }
  if (cnt == 0) return 0.0;
  double mse = acc / (double)cnt;
  double sim = 1.0 - mse;
  if (sim < 0.0) sim = 0.0;
  if (sim > 1.0) sim = 1.0;
  return sim;
}

inline double moving_average(double prev, double current, double alpha = 0.1) {
  return alpha * current + (1.0 - alpha) * prev;
}

} // namespace torus_metrics
