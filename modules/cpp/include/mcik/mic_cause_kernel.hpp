#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <type_traits>
#include <utility>
#include <vector>

namespace mcik {

/**
 * Simple deterministic 1D lattice used to illustrate the Micro-Cause Influence Kernel (MCIK)
 * workflow.  The update rule follows the paper's alpha/beta parametrisation:
 *
 *   g_{i}^{t+1} = tanh(alpha * g_{i}^{t} + beta * (g_{i-1}^{t} + g_{i+1}^{t}))
 *
 * Periodic boundary conditions close the lattice loop so the kernels remain stable.
 * The `derive()` routine exposes a Jacobian column that functions as a discrete
 * micro-cause influence kernel for the current lattice state.
 */
template <typename T = double>
class Lattice1D {
  static_assert(std::is_floating_point_v<T>,
                "Lattice1D requires a floating point scalar type");

 public:
  using value_type = T;

  Lattice1D(std::size_t size, T alpha, T beta)
      : size_(size),
        alpha_(alpha),
        beta_(beta),
        state_(size, static_cast<T>(0)),
        kernel_(size, std::vector<T>(size, static_cast<T>(0))) {
    if (size_ < 3) {
      throw std::invalid_argument("Lattice1D expects at least three sites.");
    }
  }

  std::size_t size() const noexcept { return size_; }

  std::vector<T>& g() noexcept { return state_; }
  const std::vector<T>& g() const noexcept { return state_; }

  void reset(const std::vector<T>& state) {
    if (state.size() != size_) {
      throw std::invalid_argument("reset() expects a vector matching lattice size.");
    }
    state_ = state;
  }

  void forward() { state_ = apply_rule(state_); }

  void forward_steps(std::size_t steps) {
    for (std::size_t i = 0; i < steps; ++i) {
      forward();
    }
  }

  void derive() { compute_kernel(); }

  const std::vector<std::vector<T>>& kernel() const noexcept { return kernel_; }

  std::vector<T> column(std::size_t index) const {
    if (index >= size_) {
      throw std::out_of_range("Column index is out of bounds.");
    }
    std::vector<T> col(size_);
    for (std::size_t row = 0; row < size_; ++row) {
      col[row] = kernel_[row][index];
    }
    return col;
  }

 private:
  std::vector<T> apply_rule(const std::vector<T>& input) const {
    std::vector<T> next(size_);
    for (std::size_t i = 0; i < size_; ++i) {
      const std::size_t left = (i == 0) ? size_ - 1 : i - 1;
      const std::size_t right = (i + 1) % size_;
      const T linear = alpha_ * input[i] + beta_ * (input[left] + input[right]);
      next[i] = std::tanh(linear);
    }
    return next;
  }

  void compute_kernel() {
    const T eps = std::sqrt(std::numeric_limits<T>::epsilon());
    std::vector<T> base_state = state_;
    for (std::size_t j = 0; j < size_; ++j) {
      std::vector<T> plus = base_state;
      std::vector<T> minus = base_state;
      plus[j] += eps;
      minus[j] -= eps;
      const auto next_plus = apply_rule(plus);
      const auto next_minus = apply_rule(minus);
      for (std::size_t i = 0; i < size_; ++i) {
        kernel_[i][j] = (next_plus[i] - next_minus[i]) / (static_cast<T>(2) * eps);
      }
    }
  }

  std::size_t size_;
  T alpha_;
  T beta_;
  std::vector<T> state_;
  std::vector<std::vector<T>> kernel_;
};

}  // namespace mcik
