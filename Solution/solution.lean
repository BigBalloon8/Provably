import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat Int

theorem irrational_sqrt2 : ¬∃ (a b : ℤ), b ≠ 0 ∧ a.natAbs.gcd b.natAbs = 1 ∧ (a : ℝ) / b = Real.sqrt 2 := by
  have h_main : ∀ (a b : ℤ), b ≠ 0 → a.natAbs.gcd b.natAbs = 1 → (a : ℝ) / b = Real.sqrt 2 → False := by
    intro a b hb hgcd h
    have h₁ : (a : ℝ) / b = Real.sqrt 2 := h
    have h₂ : (a : ℝ) = b * Real.sqrt 2 := by
      have h₃ : b ≠ 0 := by simpa using hb
      field_simp [h₃] at h₁
      exact h₁
    have h₃ : (a : ℝ) = b * Real.sqrt 2 := h₂
    have h₄ : (a : ℝ) ^ 2 = (b * Real.sqrt 2) ^ 2 := by rw [h₃]
    have h₅ : (a : ℝ) ^ 2 = 2 * (b : ℝ) ^ 2 := by
      rw [h₄]
      ring_nf
      rw [Real.sq_sqrt (by norm_num : (0 : ℝ) ≤ 2)]
      ring
    have h₇ : (a : ℤ) ^ 2 = 2 * (b : ℤ) ^ 2 := by
      have h₈ : (a : ℝ) ^ 2 = 2 * (b : ℝ) ^ 2 := h₅
      norm_cast at h₈
    have h₈ : 2 ∣ a ^ 2 := by
      use b ^ 2
      linarith
    have h₉ : 2 ∣ a := by
      have h₁₀ : 2 ∣ a ^ 2 := h₈
      exact (Int.prime_two.dvd_of_dvd_pow h₁₀)
    have h₁₀ : a % 2 = 0 := by
      omega
    have h₁₁ : ∃ k : ℤ, a = 2 * k := by
      use a / 2
      have h₁₂ : a % 2 = 0 := h₁₀
      have h₁₃ : a = 2 * (a / 2) := by
        omega
      linarith
    rcases h₁₁ with ⟨k, hk⟩
    have h₁₂ : (a : ℤ) ^ 2 = 2 * (b : ℤ) ^ 2 := h₇
    rw [hk] at h₁₂
    have h₁₃ : (2 * k : ℤ) ^ 2 = 2 * (b : ℤ) ^ 2 := by
      linarith
    have h₁₄ : 4 * (k : ℤ) ^ 2 = 2 * (b : ℤ) ^ 2 := by
      ring_nf at h₁₃ ⊢
      nlinarith
    have h₁₅ : 2 * (k : ℤ) ^ 2 = (b : ℤ) ^ 2 := by
      nlinarith
    have h₁₆ : 2 ∣ b ^ 2 := by
      use k ^ 2
      linarith
    have h₁₇ : 2 ∣ b := by
      have h₁₈ : 2 ∣ b ^ 2 := h₁₆
      exact Int.prime_two.dvd_of_dvd_pow h₁₈
    have h₁₈ : b % 2 = 0 := by
      omega
    have h₁₉ : ∃ m : ℤ, b = 2 * m := by
      use b / 2
      have h₂₁ : b = 2 * (b / 2) := by
        omega
      linarith
    rcases h₁₉ with ⟨m, hm⟩
    have h₂₀ : a.natAbs.gcd b.natAbs = 1 := hgcd
    have h₂₆ : 2 ∣ a.natAbs := by
      have h₂₇ : 2 ∣ a := by omega
      rw [Int.coe_nat_dvd]
      exact Int.natCast_dvd_natCast.mpr (Int.natAbs_dvd.mpr h₂₇)
    have h₂₇ : 2 ∣ b.natAbs := by
      have h₂₈ : 2 ∣ b := by omega
      rw [Int.coe_nat_dvd]
      exact Int.natCast_dvd_natCast.mpr (Int.natAbs_dvd.mpr h₂₈)
    have h₂₈ : 2 ∣ a.natAbs.gcd b.natAbs := by
      exact Nat.dvd_gcd h₂₆ h₂₇
    have h₂₉ : a.natAbs.gcd b.natAbs ≥ 2 := by
      by_contra h
      have h₃₇ : a.natAbs.gcd b.natAbs ≤ 1 := by linarith
      have h₃₈ : a.natAbs.gcd b.natAbs = 0 ∨ a.natAbs.gcd b.natAbs = 1 := by omega
      cases h₃₈ with
      | inl h₃₈ => simp_all; omega
      | inr h₃₈ => simp_all; omega
    omega
  intro h
  rcases h with ⟨a, b, hb, hgcd, h⟩
  have h₁ := h_main a b hb hgcd h
  exact h₁
