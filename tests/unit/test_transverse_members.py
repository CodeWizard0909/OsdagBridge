from osdagbridge.core.bridge_types.plate_girder.results_data import transverse_member_lines


def _grillage(n_stations=3, girder_z=(0.0, 2.5, 5.0), edge_z=(-1.0, 6.0)):
    """Plain grillage: x = span, z = width, y = 0. Longitudinal lines at every z, cross members at every station."""
    zs = sorted(girder_z + edge_z)
    nodes, members, tag = {}, {}, 1
    nid = lambda s, k: s * 100 + k
    for s in range(n_stations):
        for k, z in enumerate(zs):
            nodes[nid(s, k)] = [s * 5.0, 0.0, z]
    for k in range(len(zs)):                      # longitudinal
        for s in range(n_stations - 1):
            members[tag] = [nid(s, k), nid(s + 1, k)]; tag += 1
    for s in range(n_stations):                   # transverse, including overhang strips to the edge beams
        for k in range(len(zs) - 1):
            members[tag] = [nid(s, k), nid(s, k + 1)]; tag += 1
    return nodes, members


def test_lines_keep_only_girder_to_girder_members_per_station():
    nodes, members = _grillage()
    lines = transverse_member_lines(nodes, members, edge_dist=1.0)

    assert len(lines) == 3                                   # one per station: ED1, CB1, ED2
    for s, line in enumerate(lines):
        assert len(line) == 2                                # 3 girders -> 2 bays; overhang strips dropped
        assert {nodes[n][0] for e in line for n in members[e]} == {s * 5.0}
        assert members[line[0]][1] == members[line[1]][0]    # chained across the width
        assert all(0.0 <= nodes[n][2] <= 5.0 for e in line for n in members[e])


def test_without_overhang_outer_lines_are_girders():
    nodes, members = _grillage(edge_z=())
    lines = transverse_member_lines(nodes, members, edge_dist=0.0)
    assert [len(line) for line in lines] == [2, 2, 2]
