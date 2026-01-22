from jpr_lib import vladar_formula
import numpy as np
import matplotlib.pyplot as plt

def plot_curve(
    x,
    y,
    title="",
    xlabel="x",
    ylabel="y",
    show_points=False,
    linewidth=2,
    point_size=40,
    grid=True,
    legend_label=None,
    figsize=(9, 5)
):
    """
    Trace une courbe standardisée.
    x : liste ou array des abscisses
    y : liste ou array des ordonnées
    """

    plt.figure(figsize=figsize)

    # Courbe principale
    plt.plot(x, y, linewidth=linewidth, label=legend_label)

    # Optionnel : points visibles
    if show_points:
        plt.scatter(x, y, s=point_size)

    # Titres et labels
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    # Grille optionnelle
    if grid:
        plt.grid(True)

    # Légende si demandée
    if legend_label:
        plt.legend()

    plt.tight_layout()
    plt.show()

# ---------------------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Torn Stat Gain Calculator ===")

    # Values to be used
    stat_to_train = "defense"      # "strength", "speed", "dexterity", "defense"
    current_stat_value = 5_000_000_000  # current stat
    gym_bonus = 8                  # gym dots / 10 (typically 7.3 for Georges, 8 for Isomaya)
    energy_per_train = 50.0        # train cost  ((typically 10 for Georges, 50 for Isomaya)
    # happy = 5000                   # starting happy
    # Gym perks in percent
    perks_percent = [15, 2, 1, 1, 0, 0]  # faction, property, education specific, general, job, book
    happy_list = np.arange(1400.,6200.,200.)

    delta_list = [vladar_formula(
        stat_key=stat_to_train,
        current_stat=current_stat_value,
        gym_bonus=gym_bonus,
        energy_per_train=energy_per_train,
        happy=float(happy),
        perks_percent=perks_percent,
        include_random=False) for happy in happy_list]

    happy_ref = 5000
    delta_ref = vladar_formula(
        stat_key=stat_to_train,
        current_stat=current_stat_value,
        gym_bonus=gym_bonus,
        energy_per_train=energy_per_train,
        happy=(happy_ref),
        perks_percent=perks_percent,
        include_random=False)

    delta_percent = [100*(delta-delta_ref)/delta_ref for delta in delta_list]

    plot_curve(happy_list, delta_percent, xlabel="happy", ylabel="%", title="energy gain variation vs happy\nfor any stat > 50m, happy base 5000" )

    # # Compute the gain (all keyword arguments)
    # delta = vladar_formula(
    #     stat_key=stat_to_train,
    #     current_stat=current_stat_value,
    #     gym_bonus=gym_bonus,
    #     energy_per_train=energy_per_train,
    #     happy=happy,
    #     perks_percent=perks_percent,
    #     include_random=False
    # )
    # # Print results
    # print(f"Stat trained   : {stat_to_train}")
    # print(f"Delta stat     : {delta:,.10f}")
