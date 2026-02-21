import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat

theorem intersection_of_subgroups_of_prime_order (G : Type*) [Group G] (H K : Subgroup G)
    (hH : Nat.card H = 65) (hK : Nat.card K = 56) : Nat.card (H ⊓ K) = 1 := by
  have h1 : Nat.card (H ⊓ K) ∣ Nat.card H := by
    apply?
  have h2 : Nat.card (H ⊓ K) ∣ Nat.card K := by
    apply?
  have h3 : Nat.card (H ⊓ K) ∣ Nat.gcd (Nat.card H) (Nat.card K) := by
    apply?
  have h4 : Nat.gcd (Nat.card H) (Nat.card K) = 1 := by
    simp_all [Nat.gcd_eq_right]
    <;> norm_num
  have h5 : Nat.card (H ⊓ K) = 1 := by
    simp_all [Nat.dvd_one]
  exact h5