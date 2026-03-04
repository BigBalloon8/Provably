import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat

theorem ratio_test_convergence
    (x : ℝ) (hx0 : 0 < x) (hx1 : x < 1)
    (a : ℕ → ℝ) (ha_pos : ∀ n, 0 < a n)
    (ha_ratio : ∀ n, a (n + 1) / a n < x) :
    Summable a := by
  -- Step 0: Derive a(n+1) < x * a(n)
  have hratio : ∀ n, a (n + 1) < x * a n := by
    intro n
    have h := ha_ratio n
    have hpos := ha_pos n
    have h2 : a (n + 1) / a n * a n < x * a n :=
      mul_lt_mul_of_pos_right h hpos
    rwa [div_mul_cancel₀ _ (ne_of_gt hpos)] at h2
  -- Step 1: Inductive bound a n ≤ a 0 * x ^ n
  have hbound : ∀ n, a n ≤ a 0 * x ^ n := by
    intro n
    induction n with
    | zero => simp
    | succ k ih =>
      have hlt : a (k + 1) < a 0 * x ^ (k + 1) :=
        calc a (k + 1) < x * a k := hratio k
          _ ≤ x * (a 0 * x ^ k) := by exact mul_le_mul_of_nonneg_left ih (le_of_lt hx0)
          _ = a 0 * x ^ (k + 1) := by ring
      exact le_of_lt hlt
  -- Step 2: Geometric series is summable
  have hgeom : Summable (fun n => a 0 * x ^ n) :=
    (summable_geometric_of_lt_one (le_of_lt hx0) hx1).mul_left (a 0)
  -- Step 3: Comparison test
  exact Summable.of_nonneg_of_le
    (fun n => le_of_lt (ha_pos n))
    hbound
    hgeom