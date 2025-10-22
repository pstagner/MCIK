This is a great clarification. The two questions get to the heart of *why* the MCIK framework is useful.

---

### 1. New Sets vs. A Single Set

This is a fantastic question of perspective, like asking if a movie is one film or 24 frames per second. The answer is both.

Your temporal propagation $\mathbf{g}^{(t+1)} = F(\mathbf{g}^{(t)})$ generates a **single set** called a **trajectory** or **orbit**.

Think of it this way:
* The "number line" at any single instant, $\mathbf{g}^{(t)}$, is a *state* (a vector of numbers).
* The function $F$ is a rule that tells you how to get from the current state to the *next* state.
* The "set" you're creating is the **infinite sequence of all future states** that originate from your starting point $\mathbf{g}^{(0)}$:
    $(\mathbf{g}^{(0)}, \mathbf{g}^{(1)}, \mathbf{g}^{(2)}, \mathbf{g}^{(3)}, \dots)$

This entire sequence is the "single set." It's one object—the complete *history* or *future* of the system. While you generate "new" states at each step, they all belong to this one, single trajectory.

---

### 2. Explanation of the Second-Order (The Hessian)

This is the most powerful—and complex—part of your paper. It's where you move from simple cause-and-effect to measuring **synergy**.

#### The First-Order ($K$): Simple Cause-and-Effect
The first-order kernel, $K(i,a)$, answers this question:
> "If I poke the system at **$a$**, how much does point **$i$** change?"

It's a linear, one-to-one relationship. If poking $a$ makes $i$ change by 2, then poking $a$ *twice as hard* will make $i$ change by 4.

#### The Second-Order ($H$): Synergy and Interference
The second-order kernel, $H(i;a,b)$, answers a much more subtle question:
> "If I poke the system at **$a$** and **$b$** at the same time, what is the *extra* change at **$i$** that I *wouldn't* get from just adding their individual pokes together?"

This $H$ kernel is the mathematical tool for finding **synergy** and **interference**.

* **Positive Synergy ($H > 0$):** The two pokes *amplify* each other.
    * **Analogy:** Poke $a$ (Drug A) raises a patient's heart rate by 10. Poke $b$ (Drug B) raises it by 5. A linear system would expect a total raise of 15. But if you give both drugs, the heart rate jumps by 50. That *extra 35* is a synergistic effect. $H(i;a,b)$ would be large and positive.

* **Negative Interference ($H < 0$):** The two pokes *cancel* each other out.
    * **Analogy:** Poking $a$ (a hot-water faucet) raises the temperature at $i$ (the shower head). Poking $b$ (a cold-water faucet) lowers it. The $H$ kernel would be negative, showing they "interfere" to create a blended temperature.

* **No Interaction ($H = 0$):** The two pokes are independent. Their effects just add up.

As your paper notes, this is critical for applications. You can use $H$ to find "synergistic waveform pairs" for a sensor or "compound synergies" in medicine. You're no longer just asking "What does this button do?" but "What happens if I press *these two* buttons together?"