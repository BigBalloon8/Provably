import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat

theorem intersection_of_subgroups_is_trivial (G : Type*) [Group G] (H K : Subgroup G) 
  (hH : Nat.card H = 65) (hK : Nat.card K = 56) : H ∩ K = ⊥ := by
  have h1 : Nat.card (H ∩ K) ∣ 65 := by sorry
  have h2 : Nat.card (H ∩ K) ∣ 56 := by sorry
  have h3 : Nat.card (H ∩ K) = 1 := by sorry
  have h4 : H ∩ K = ⊥ := by sorry
  exact h4