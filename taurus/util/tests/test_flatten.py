from taurus.entity.bounds.categorical_bounds import CategoricalBounds
from taurus.entity.object import ProcessSpec, MaterialSpec, IngredientSpec, ProcessRun, \
    MaterialRun, IngredientRun
from taurus.entity.template.condition_template import ConditionTemplate
from taurus.entity.template.process_template import ProcessTemplate
from taurus.util import flatten, recursive_flatmap


def test_flatten_bounds():
    """Test that flatten works when the objects contain other objects."""
    bounds = CategoricalBounds(categories=["foo", "bar"])
    template = ProcessTemplate(
        "spam",
        conditions=[(ConditionTemplate(name="eggs", bounds=bounds), bounds)]
    )
    spec = ProcessSpec(name="spec", template=template)

    flat = flatten(spec)
    assert len(flat) == 2, "Expected 2 flattened objects"


def test_flatten_empty_history():
    """Test that flatten works when the objects are empty and go through a whole history."""
    procured = ProcessSpec(name="procured")
    input = MaterialSpec(name="foo", process=procured)
    transform = ProcessSpec(name="transformed")
    ingredient = IngredientSpec(name="input", material=input, process=transform)

    procured_run = ProcessRun(name="procured", spec=procured)
    input_run = MaterialRun(name="foo", process=procured_run, spec=input)
    transform_run = ProcessRun(name="transformed", spec=transform)
    ingredient_run = IngredientRun(
        name="input", material=input_run, process=transform_run, spec=ingredient)

    assert len(flatten(procured)) == 0
    assert len(flatten(input)) == 1
    assert len(flatten(ingredient)) == 3
    assert len(flatten(transform)) == 3

    assert len(flatten(procured_run)) == 1
    assert len(flatten(input_run)) == 3
    assert len(flatten(ingredient_run)) == 7
    assert len(flatten(transform_run)) == 7


def test_flatmap_skip_ordering():
    """Test that the chronological setting is obeyed."""
    # The writeable link is ingredient -> process, but the chronological link is
    # process -> ingredient
    proc = ProcessRun(name="foo")
    IngredientRun(name="bar", process=proc)

    assert len(recursive_flatmap(proc, lambda x: [x], chronological=True)) == 2
    assert len(recursive_flatmap(proc, lambda x: [x], chronological=False)) == 0
