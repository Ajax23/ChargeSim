################################################################################
# MC Class                                                                     #
#                                                                              #
"""Monte Carlo algorithm for calculating occupancy probability."""
################################################################################


import sys
import random

from chargesim.probability import P


class MC:
    """This class run a Monte Carlo simulation. Probability of every node is the
    sum of given probabilities from the poi list. This means, nodes intersecting
    multiple poi.s have a higher probability than the single pois.

    Parameters
    ----------
    topo : Topology
        Topology object
    users : list
        List of user objects
    pois : list, optional
        List of poi objects
    node_p : dictionary, float, optional
        Probability of all nodes not covered by pois each hour each weekday,
        either a float for the same probability each hour, dictionary of hours
        for same hour distribution for all days, a dictionary of days for the
        same hour probability for different days, or a dictionary of days each
        with a dictionary of hours
    """
    def __init__(self, topo, users, pois=[], node_p=1):
        # Initialize
        self._topo = topo
        self._users = users
        node_p = P(node_p)

        # Process pois
        p = {}
        # max_p = 0
        for poi in pois:
            for node in poi.get_nodes():
                if node not in p:
                    p[node] = P(p=poi.get_p())
                else:
                    temp_p = {}
                    for day in range(7):
                        temp_p[day] = {}
                        for hour in range(24):
                            temp_p[day][hour] = p[node].get_p_hour(day, hour)+poi.get_p_hour(day, hour)
                            # max_p = temp_p[day][hour] if temp_p[day][hour]>max_p else max_p
                    p[node] = P(p=temp_p)

        # Normalize if probability is greater than 1
        # if max_p > 1:
        #     for node in p:
        #         p[node] = P(p={day: {hour: p[node].get_p_hour(day, hour)/max_p for hour in range(24)} for day in range(7)})

        # Fill empty nodes
        for node in topo.get_nodes():
            if node not in p:
                p[node] = node_p

        self._nodes = p

        # Get charging stations
        self._charge_G, self._capacity = topo.charging_station()
        self._stations = {station: 0 for station in self._capacity.keys()}

    def run(self, weeks, drivers):
        """Run Monte Carlo code.

        Parameters
        ----------
        weeks : integer
            Number of weeks to simulate
        drivers : dictionary, integer
            Number of drivers each hour, either an integer for the same hour,
            dictionary of hours or dictionary of days with a dictionary of hours

        Returns
        -------
        results : dictionary
            Node occupance
        """
        # Initialize
        progress_form = "%"+str(len(str(weeks*7)))+"i"

        # Process input
        if isinstance(drivers, int):
            drivers = {day: {hour: drivers for hour in range(24)} for day in range(7)}
        elif isinstance(drivers, dict):
            if not (0 in drivers.keys() and isinstance(drivers[0], dict)):
                if 23 in drivers.keys():
                    drivers = {day: {hour: drivers[hour] for hour in range(24)} for day in range(7)}
                elif 6 in drivers.keys():
                    drivers = {day: {hour: drivers[day] for hour in range(24)} for day in range(7)}
                else:
                    print("MC: Invalid dirver input...")
                    return
        else:
            print("MC: Invalid dirver input...")
            return

        # Run through weeks
        for week in range(weeks):
            # Run through days
            for day in range(7):
                # Run through hours
                for hour in range(24):
                    # Run through dirvers
                    for driver in range(drivers[day][hour]):
                        # Choose random user
                        user = random.choice(self._users)
                        rand = random.uniform(0, 1)
                        # User MC step
                        if rand <= user.get_p_hour(day, hour):
                            # Choose random node
                            node = random.choice(list(self._nodes.keys()))
                            rand = random.uniform(0, 1)
                            # Poi MC step
                            if rand <= self._nodes[node].get_p_hour(day, hour):
                                # Calculate distance to nearest charging station
                                dest, dist = self._topo.dist_poi(node, self._charge_G)

                                self._stations[dest] += 1

                # Progress
                sys.stdout.write("Finished day "+progress_form%(week*7+day+1)+"/"+progress_form%(weeks*7)+"...\r")
                sys.stdout.flush()
        print()
