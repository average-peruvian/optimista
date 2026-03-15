# Stochastic optimization with Differential Evolution

Parameters:
- Painting -> The Garden of Earthlly Delights: 7793x4409px
- Notebook -> 100H Squared Notebook Pagoda: 594x832px
- $\rho^{*}$: painting's width/height ratio -> 1.768

Variables:
- $C \in N^{+}$: amount of books in columns
- $R \in N^{+}$: amount of books in rows
- $\delta \in \{0,1\}$: book orientation (0 = 0°, 1 = 90°)

Equations: 
- $w(\delta) = 594(1-\delta) + 832(\delta)$: defines width depending on rotation.
- $h(\delta) = 594(\delta) + 832(1- \delta)$: defines height depending on rotation.
- $\rho = |\frac{C*w(\delta)}{R*h(\delta)}|$: composed books' width/height ratio.

Objective:  minimize  $N = C * R$, being N the total amount of notebooks.

Abiding to the following restrictions:
- |$\rho - \rho^{*}| \leq \epsilon * \rho^{*}$: the absolute difference of the composed books' ratio and the painting's ratio is less than an admissible distance threshold.
- $\epsilon = 0.05$: the tolerance of the admissible threshold is 5%