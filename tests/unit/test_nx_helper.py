import pytest
import nx_helper as nxh

@pytest.fixture
def simple_dag():
    dag = nxh.Dag()
    dag.add_edges_from([("A","B"),("B","C"),("A","D"),("D","C")])
    return dag

@pytest.fixture
def cyclic_graph():
    G = nxh.nx.DiGraph()
    G.add_edges_from([("A","B"),("B","C"),("C","A")])
    return G


def test_find_root_node_single_root(simple_dag):
    root = nxh.find_root_node(simple_dag)
    assert root == "A"

def test_find_root_node_no_root():
    G = nxh.nx.DiGraph()
    G.add_edge("A","B")
    G.add_edge("B","A")  
    assert nxh.find_root_node(G) is None

def test_remove_back_edges_on_cycle_returns_acyclic(cyclic_graph):
    H = nxh.remove_back_edges_to_make_dag(cyclic_graph, "A")
    assert isinstance(H, nxh.nx.DiGraph)
    assert nxh.has_cycles(H) is False
    assert ("A","B") in H.edges() and ("B","C") in H.edges()

def test_remove_back_edges_on_dag_is_noop(simple_dag):
    H = nxh.remove_back_edges_to_make_dag(simple_dag, "A")
    assert set(H.edges()) == set(simple_dag.edges())

def test_write_dag_to_dot_file_creates_dot(simple_dag, tmp_path):
    out = tmp_path / "g.dot"
    nxh.write_dag_to_dot_file(simple_dag, str(out), dag_name="G")
    text = out.read_text()
    assert "digraph" in text and "A" in text and "B" in text

def test_write_dag_to_dot_file_highlighted_edges(tmp_path):
    dag = nxh.Dag()
    dag.add_edges_from([("A","B"),("B","C")])
    out = tmp_path / "g.dot"
    nxh.write_dag_to_dot_file(
        dag, str(out), highlighted_edges=[("A","B")], highlight_color="blue"
    )
    txt = out.read_text()
    assert "A" in txt and "B" in txt
    assert "blue" in txt


def test_construct_dag_reads_dot_and_builds_dag(tmp_path):
    dot = 'digraph H { A -> B; B -> C; A -> C; }'
    p = tmp_path / "h.dot"
    p.write_text(dot)
    dag, flag = nxh.construct_dag(str(p))
    assert isinstance(dag, nxh.Dag)
    assert isinstance(flag, bool)  
    assert set(dag.edges()) == {("A","B"), ("B","C"), ("A","C")}

def test_construct_dag_bad_path_raises(tmp_path):
    bad = tmp_path / "nope.dot"
    with pytest.raises(nxh.GameTimeError):
        nxh.construct_dag(str(bad))

def test_num_paths_counts_multiple_paths(simple_dag):
    assert nxh.num_paths(simple_dag, "A", "C") == 2

def test_num_paths_identity_path(simple_dag):
    assert nxh.num_paths(simple_dag, "A", "A") == 1

def test_num_paths_invalid_source_raises(simple_dag):
    with pytest.raises(nxh.GameTimeError):
        nxh.num_paths(simple_dag, "C", "A")

def test_get_random_path_returns_valid_source_to_sink(simple_dag):
    path = nxh.get_random_path(simple_dag, "A", "C")
    assert path[0] == "A" and path[-1] == "C"
    assert all((u, v) in simple_dag.edges() for u, v in zip(path, path[1:]))

def test_get_random_path_monkeypatched_determinism(simple_dag, monkeypatch):
    monkeypatch.setattr(nxh, "randrange", lambda n: 0)
    path = nxh.get_random_path(simple_dag, "A", "C")
    assert path in (["A","B","C"], ["A","D","C"])  
