import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat

theorem group_abelian_iff_square_condition (G : Type*) [Group G] :
  (∀ g h : G, (g * h) ^ 2 = g ^ 2 * h ^ 2) ↔ (∀ g h : G, g * h = h * g) := by
  constructor
  · -- (1) ⟹ (2): Assume (g * h)² = g² * h² for all g, h, prove G is abelian
    intro h_square g h
    have h1 : (g * h) ^ 2 = g ^ 2 * h ^ 2 := h_square g h
    have h2 : g * h = h * g := by
      have h3 : (g * h) ^ 2 = g ^ 2 * h ^ 2 := h1
      have h4 : (g * h) * (g * h) = g * g * (h * h) := by
        simp [pow_two, mul_assoc] at h3 ⊢
        <;> simp_all [mul_assoc]
        <;> aesop
      have h5 : g * h = h * g := by
        have h6 := h4
        simp [mul_assoc] at h6
        rw [← mul_right_inj (g⁻¹ : G)] at h6 ⊢
        simp_all [mul_assoc, mul_inv_self, one_mul, mul_one]
        <;>
        simp_all [mul_assoc, mul_inv_self, one_mul, mul_one]
        <;>
        aesop
      exact h5
    exact h2
  · -- (2) ⟹ (1): Assume G is abelian, prove (g * h)² = g² * h² for all g, h
    intro h_abelian g h
    have h1 : g * h = h * g := h_abelian g h
    have h2 : (g * h) ^ 2 = g ^ 2 * h ^ 2 := by
      have h3 : (g * h) ^ 2 = g ^ 2 * h ^ 2 := by
        calc
          (g * h) ^ 2 = (g * h) * (g * h) := by simp [pow_two]
          _ = g * (h * g) * h := by
            simp [mul_assoc, h1]
            <;>
            simp_all [mul_assoc]
            <;>
            aesop
          _ = g * (g * h) * h := by
            simp [h1]
            <;>
            simp_all [mul_assoc]
            <;>
            aesop
          _ = (g * g) * (h * h) := by
            simp [mul_assoc]
            <;>
            simp_all [mul_assoc]
            <;>
            aesop
          _ = g ^ 2 * h ^ 2 := by
            simp [pow_two]
            <;>
            simp_all [mul_assoc]
            <;>
            aesop
      exact h3
    exact h2