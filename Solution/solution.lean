import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat

theorem bernoulli_inequality (x : ℝ) (n : ℕ) (hx : x ≥ 0) : (1 + x)^n ≥ 1 + n * x := by
  induction n with
  | zero => simp
  | succ n ih =>
    have hx1 : 0 ≤ 1 + x := by linarith
    have h_cast : (↑(n + 1) : ℝ) = ↑n + 1 := by push_cast; ring
    rw [pow_succ]
    have h2 : (1 + x) ^ n * (1 + x) ≥ (1 + ↑n * x) * (1 + x) :=
      mul_le_mul_of_nonneg_right ih hx1
    have h3 : 0 ≤ ↑n * (x * x) := by positivity
    rw [h_cast]
    nlinarith