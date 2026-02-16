import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat

theorem series_converges (x : ℝ) (hx : 0 < x ∧ x < 1) (a : ℕ → ℝ) (ha : ∀ n, 0 < a n) (h : ∀ n, a (n + 1) / a n < x) : 
  Summable a := by
  have h₁ : ∀ n, a (n + 1) < x ^ n * a 1 := by
    sorry
  have h₂ : ∀ n, a n ≤ a 1 * x ^ (n - 1) := by
    sorry
  have h₃ : Summable a := by
    sorry
  sorry