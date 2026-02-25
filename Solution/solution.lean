import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat

theorem group_abelian_iff_square_condition (G : Type*) [Group G] :
  (∀ g h : G, g * h = h * g) ↔ (∀ g h : G, (g * h) ^ 2 = g ^ 2 * h ^ 2) := by
  have h_forward : (∀ g h : G, g * h = h * g) → (∀ g h : G, (g * h) ^ 2 = g ^ 2 * h ^ 2) := by
    sorry
  have h_backward : (∀ g h : G, (g * h) ^ 2 = g ^ 2 * h ^ 2) → (∀ g h : G, g * h = h * g) := by
    sorry
  have h_main : (∀ g h : G, g * h = h * g) ↔ (∀ g h : G, (g * h) ^ 2 = g ^ 2 * h ^ 2) := by
    sorry
  exact h_main